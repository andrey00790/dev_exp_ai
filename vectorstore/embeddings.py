"""
OpenAI embeddings pipeline for document vectorization.
Enhanced with standardized async patterns for enterprise reliability.
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional
import openai
import os
from dataclasses import dataclass
import tiktoken
import asyncio

# Import standardized async patterns
from app.core.async_utils import (
    AsyncTimeouts, 
    with_timeout, 
    async_retry,
    safe_gather,
    create_background_task
)
from app.core.exceptions import AsyncTimeoutError, AsyncRetryError

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Result of embedding operation."""
    text: str
    vector: List[float]
    token_count: int
    cost_estimate: float

class OpenAIEmbeddings:
    """OpenAI embeddings service for text vectorization."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI embeddings client.
        
        Args:
            api_key: OpenAI API key (defaults to env variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found. Embeddings will use mock data.")
        
        self.model = "text-embedding-ada-002"
        self.max_tokens = 8192  # Max tokens for ada-002
        self.cost_per_1k_tokens = 0.0001  # USD per 1k tokens
        
        # Token encoder for token counting
        try:
            self.encoder = tiktoken.encoding_for_model(self.model)
        except:
            # Fallback encoder
            self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.error(f"Token counting failed: {e}")
            # Rough estimate: 1 token ≈ 4 chars
            return len(text) // 4
    
    def split_text_by_tokens(self, text: str, max_tokens: int = None) -> List[str]:
        """
        Split text into chunks that fit within token limits.
        
        Args:
            text: Input text to split
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
        if max_tokens is None:
            max_tokens = self.max_tokens - 100  # Safety margin
        
        try:
            tokens = self.encoder.encode(text)
            chunks = []
            
            for i in range(0, len(tokens), max_tokens):
                chunk_tokens = tokens[i:i + max_tokens]
                chunk_text = self.encoder.decode(chunk_tokens)
                chunks.append(chunk_text)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Text splitting failed: {e}")
            # Fallback: split by characters
            chunk_size = max_tokens * 4  # Rough estimate
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    
    @async_retry(
        max_attempts=3, 
        delay=1.0, 
        backoff=2.0,
        exceptions=(Exception,)  # Catch all exceptions for OpenAI API calls
    )
    async def embed_text(self, text: str) -> Optional[EmbeddingResult]:
        """
        Generate embedding for single text.
        Enhanced with timeout protection and retry logic.
        
        Args:
            text: Input text to embed
            
        Returns:
            EmbeddingResult or None if failed
            
        Raises:
            AsyncTimeoutError: If embedding generation times out
        """
        if not self.api_key:
            # Mock embedding for testing
            return self._mock_embedding(text)
        
        try:
            return await with_timeout(
                self._embed_text_internal(text),
                AsyncTimeouts.EMBEDDING_GENERATION,  # 30 seconds for embedding
                f"Embedding generation timed out (text length: {len(text)}, tokens: {self.count_tokens(text)})",
                {
                    "text_length": len(text),
                    "estimated_tokens": self.count_tokens(text),
                    "model": self.model
                }
            )
            
        except AsyncTimeoutError as e:
            logger.error(f"❌ Embedding generation timed out: {e}")
            return None
        except AsyncRetryError as e:
            logger.error(f"❌ Embedding generation failed after retries: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            return None
    
    async def _embed_text_internal(self, text: str) -> EmbeddingResult:
        """Internal embedding method without timeout wrapper"""
        # Count tokens
        token_count = self.count_tokens(text)
        
        if token_count > self.max_tokens:
            logger.warning(f"⚠️ Text too long ({token_count} tokens), truncating to {self.max_tokens}")
            text = self.split_text_by_tokens(text, self.max_tokens)[0]
            token_count = self.count_tokens(text)
        
        logger.debug(f"🔄 Generating embedding for text ({token_count} tokens)")
        
        # Generate embedding with OpenAI API
        response = await openai.Embedding.acreate(
            model=self.model,
            input=text
        )
        
        vector = response['data'][0]['embedding']
        cost_estimate = (token_count / 1000) * self.cost_per_1k_tokens
        
        logger.debug(f"✅ Embedding generated: {len(vector)} dimensions, ${cost_estimate:.6f} cost")
        
        return EmbeddingResult(
            text=text,
            vector=vector,
            token_count=token_count,
            cost_estimate=cost_estimate
        )
    
    @async_retry(max_attempts=2, delay=2.0, exceptions=(Exception,))
    async def embed_texts(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.
        Enhanced with concurrent processing and timeout protection.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of EmbeddingResult objects
            
        Raises:
            AsyncTimeoutError: If batch embedding times out
        """
        if not texts:
            return []
        
        try:
            # Calculate timeout based on batch size
            timeout = self._calculate_batch_embedding_timeout(texts)
            
            return await with_timeout(
                self._embed_texts_internal(texts),
                timeout,
                f"Batch embedding timed out (batch size: {len(texts)}, total chars: {sum(len(t) for t in texts)})",
                {
                    "batch_size": len(texts),
                    "total_characters": sum(len(t) for t in texts),
                    "estimated_tokens": sum(self.count_tokens(t) for t in texts[:5])  # Sample first 5
                }
            )
            
        except AsyncTimeoutError as e:
            logger.error(f"❌ Batch embedding timed out: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Batch embedding failed: {e}")
            return []
    
    async def _embed_texts_internal(self, texts: List[str]) -> List[EmbeddingResult]:
        """Internal batch embedding method with concurrent processing"""
        logger.info(f"🔄 Generating embeddings for {len(texts)} texts concurrently...")
        
        # Process embeddings concurrently with limits
        embedding_tasks = [
            self.embed_text(text)
            for text in texts
        ]
        
        # Execute with concurrency limits to avoid rate limiting
        max_concurrency = min(10, len(texts))  # Limit to 10 concurrent requests
        
        results_list = await safe_gather(
            *embedding_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.EMBEDDING_GENERATION * 2,  # 60 seconds for batch
            max_concurrency=max_concurrency
        )
        
        # Process results and filter out failures
        successful_results = []
        failed_count = 0
        
        for i, result in enumerate(results_list):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Embedding failed for text {i}: {result}")
                failed_count += 1
            elif result is not None:
                successful_results.append(result)
            else:
                failed_count += 1
        
        success_rate = len(successful_results) / len(texts) * 100
        logger.info(f"✅ Batch embedding completed: {len(successful_results)}/{len(texts)} successful ({success_rate:.1f}%)")
        
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count} embeddings failed in batch")
        
        return successful_results
    
    def _calculate_batch_embedding_timeout(self, texts: List[str]) -> float:
        """Calculate appropriate timeout for batch embedding"""
        base_timeout = AsyncTimeouts.EMBEDDING_GENERATION  # 30 seconds
        
        # Estimate total processing time
        total_tokens = sum(self.count_tokens(text) for text in texts[:10])  # Sample first 10
        avg_tokens = total_tokens / min(len(texts), 10)
        
        # More texts = more time, but with concurrency it's not linear
        if len(texts) > 10:
            # Concurrent processing means time grows slower than linearly
            extra_time = (len(texts) - 10) * 2  # 2 seconds per extra text
        else:
            extra_time = len(texts) * 3  # 3 seconds per text for small batches
        
        # Large tokens need more time
        if avg_tokens > 1000:
            extra_time += (avg_tokens - 1000) / 100  # 1s per extra 100 tokens average
        
        return min(base_timeout + extra_time, 300.0)  # Cap at 5 minutes
    
    def _mock_embedding(self, text: str) -> EmbeddingResult:
        """Generate mock embedding for testing."""
        # Create deterministic mock vector based on text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Generate 1536-dimensional vector (OpenAI ada-002 size)
        vector = []
        for i in range(1536):
            # Use hash to generate pseudo-random but deterministic values
            seed = int(text_hash[i % len(text_hash)], 16) + i
            value = (seed % 200 - 100) / 100.0  # Range [-1, 1]
            vector.append(value)
        
        # Normalize vector
        magnitude = sum(x * x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        
        token_count = self.count_tokens(text)
        
        return EmbeddingResult(
            text=text,
            vector=vector,
            token_count=token_count,
            cost_estimate=0.0  # No cost for mock
        )

class DocumentChunker:
    """Utility for chunking documents for embedding."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize document chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split document into overlapping chunks.
        
        Args:
            text: Document text
            metadata: Document metadata to include with each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence/paragraph boundaries
            chunk_text = text[start:end]
            
            if end < len(text):
                # Look for good break points (sentence endings)
                last_period = chunk_text.rfind('. ')
                last_newline = chunk_text.rfind('\n')
                
                break_point = max(last_period, last_newline)
                if break_point > start + self.chunk_size // 2:
                    end = start + break_point + 1
                    chunk_text = text[start:end]
            
            # Create chunk with metadata
            chunk = {
                "text": chunk_text.strip(),
                "chunk_id": chunk_id,
                "start_pos": start,
                "end_pos": end,
                **(metadata or {})
            }
            
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = end - self.overlap
            chunk_id += 1
            
            # Prevent infinite loop
            if start >= end:
                break
        
        return chunks

# Global embeddings instance
_embeddings_instance = None

def get_embeddings_service() -> OpenAIEmbeddings:
    """Get global OpenAI embeddings service."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = OpenAIEmbeddings()
    return _embeddings_instance 

"""
Embeddings module stub for testing
"""

class MockEmbeddingModel:
    """Mock embedding model for testing"""
    
    async def encode(self, texts: List[str]) -> List[List[float]]:
        """Mock encoding method"""
        return [[0.1, 0.2, 0.3] for _ in texts]


async def get_embedding_model():
    """Get mock embedding model for testing"""
    return MockEmbeddingModel() 