"""
OpenAI embeddings pipeline for document vectorization.
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional
import openai
import os
from dataclasses import dataclass
import tiktoken

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
    
    async def embed_text(self, text: str) -> Optional[EmbeddingResult]:
        """
        Generate embedding for single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            EmbeddingResult or None if failed
        """
        if not self.api_key:
            # Mock embedding for testing
            return self._mock_embedding(text)
        
        try:
            # Count tokens
            token_count = self.count_tokens(text)
            
            if token_count > self.max_tokens:
                logger.warning(f"Text too long ({token_count} tokens), truncating")
                text = self.split_text_by_tokens(text, self.max_tokens)[0]
                token_count = self.count_tokens(text)
            
            # Generate embedding
            response = await openai.Embedding.acreate(
                model=self.model,
                input=text
            )
            
            vector = response['data'][0]['embedding']
            cost_estimate = (token_count / 1000) * self.cost_per_1k_tokens
            
            return EmbeddingResult(
                text=text,
                vector=vector,
                token_count=token_count,
                cost_estimate=cost_estimate
            )
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    async def embed_texts(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of EmbeddingResult objects
        """
        results = []
        
        for text in texts:
            result = await self.embed_text(text)
            if result:
                results.append(result)
        
        return results
    
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