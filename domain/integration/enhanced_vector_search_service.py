"""
Enhanced Vector Search Service - Next-generation semantic search with intelligent graph analysis.
Integrates document relationship graphs and dynamic reranking with existing vector search.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from adapters.vectorstore.embeddings import get_embeddings_service

from app.core.async_utils import (AsyncTimeouts, async_retry, safe_gather,
                                  with_timeout)
from domain.integration.document_graph_builder import (DocumentNode,
                                                       DocumentRelation,
                                                       build_document_graph)
from domain.integration.dynamic_reranker import (ContextualScore, UserIntent,
                                                 rerank_search_results)
from app.services.vector_search_service import (SearchResult, VectorSearchService)
from models.base import SearchRequest

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSearchRequest(SearchRequest):
    """Enhanced search request with additional context parameters"""

    user_context: Optional[Dict[str, Any]] = None
    enable_graph_analysis: bool = True
    enable_dynamic_reranking: bool = True
    include_related_documents: bool = False
    max_related_per_result: int = 3


@dataclass
class EnhancedSearchResult(SearchResult):
    """Enhanced search result with relationship and scoring data"""

    contextual_score: Optional[ContextualScore] = None
    document_node: Optional[DocumentNode] = None
    related_documents: Optional[List[Dict[str, Any]]] = None
    user_intent: Optional[UserIntent] = None


class EnhancedVectorSearchService:
    """
    Enhanced vector search service combining traditional semantic search
    with intelligent document graph analysis and dynamic reranking.
    """

    def __init__(self, base_search_service: Optional[VectorSearchService] = None):
        self.base_search_service = base_search_service or VectorSearchService()
        self.embeddings_service = get_embeddings_service()

        # Cache for frequently accessed data
        self.graph_cache = {}
        self.intent_cache = {}

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def enhanced_search(
        self, request: EnhancedSearchRequest
    ) -> List[EnhancedSearchResult]:
        """
        Perform enhanced semantic search with graph analysis and dynamic reranking.

        Args:
            request: Enhanced search request with additional parameters

        Returns:
            List of enhanced search results with relationship data and improved scoring
        """
        try:
            return await with_timeout(
                self._enhanced_search_internal(request),
                AsyncTimeouts.ANALYTICS_AGGREGATION,  # 60 seconds
                f"Enhanced search timed out for query: {request.query[:50]}...",
                {
                    "query": request.query[:100],
                    "collections": request.collections,
                    "enable_graph_analysis": request.enable_graph_analysis,
                    "enable_dynamic_reranking": request.enable_dynamic_reranking,
                },
            )
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            # Fallback to basic search
            basic_results = await self.base_search_service.search(request)
            return [
                self._convert_to_enhanced_result(result) for result in basic_results
            ]

    async def _enhanced_search_internal(
        self, request: EnhancedSearchRequest
    ) -> List[EnhancedSearchResult]:
        """Internal enhanced search implementation"""

        logger.info(f"🔍 Starting enhanced search for: '{request.query}'")

        # Step 1: Perform base vector search
        logger.info("📊 Performing base vector search...")
        base_results = await self.base_search_service.search(request)

        if not base_results:
            logger.info("No base results found")
            return []

        logger.info(f"📊 Base search returned {len(base_results)} results")

        # Step 2: Build document graph (if enabled)
        document_graph = None
        if request.enable_graph_analysis and len(base_results) > 1:
            logger.info("🔗 Building document relationship graph...")
            try:
                document_graph = await build_document_graph(
                    base_results, include_semantic_analysis=True
                )
                logger.info(
                    f"🔗 Built graph with {len(document_graph)} nodes and relationships"
                )
            except Exception as e:
                logger.warning(f"Graph building failed: {e}")

        # Step 3: Dynamic reranking (if enabled)
        reranked_results = base_results
        user_intent = None

        if request.enable_dynamic_reranking:
            logger.info("🎯 Applying dynamic reranking...")
            try:
                reranked_results = await rerank_search_results(
                    base_results, request.query, request.user_context, request.limit
                )

                # Extract user intent from the first result (if available)
                if reranked_results and hasattr(
                    reranked_results[0], "contextual_score"
                ):
                    # We can infer user intent from the reranking process
                    # This is a simplified approach - in practice, we'd extract it properly
                    pass

                logger.info(f"🎯 Reranking completed, results reordered")
            except Exception as e:
                logger.warning(f"Dynamic reranking failed: {e}")

        # Step 4: Enhance results with graph data and related documents
        enhanced_results = []
        for result in reranked_results:
            enhanced_result = await self._create_enhanced_result(
                result, document_graph, request
            )
            enhanced_results.append(enhanced_result)

        # Step 5: Add related documents if requested
        if request.include_related_documents and document_graph:
            await self._add_related_documents(
                enhanced_results, document_graph, request.max_related_per_result
            )

        logger.info(
            f"✅ Enhanced search completed with {len(enhanced_results)} results"
        )
        return enhanced_results

    async def _create_enhanced_result(
        self,
        base_result: SearchResult,
        document_graph: Optional[Dict[str, DocumentNode]],
        request: EnhancedSearchRequest,
    ) -> EnhancedSearchResult:
        """Create enhanced result with additional metadata"""

        # Get document node from graph
        document_node = None
        if document_graph and base_result.doc_id in document_graph:
            document_node = document_graph[base_result.doc_id]

        # Extract contextual score if available
        contextual_score = getattr(base_result, "contextual_score", None)

        # Create enhanced result
        enhanced_result = EnhancedSearchResult(
            doc_id=base_result.doc_id,
            title=base_result.title,
            content=base_result.content,
            score=base_result.score,
            source=base_result.source,
            source_type=base_result.source_type,
            url=base_result.url,
            author=base_result.author,
            created_at=base_result.created_at,
            tags=base_result.tags,
            collection_name=base_result.collection_name,
            chunk_index=base_result.chunk_index,
            highlights=base_result.highlights,
            contextual_score=contextual_score,
            document_node=document_node,
            related_documents=None,  # Will be populated later if requested
            user_intent=None,  # Will be populated if available
        )

        return enhanced_result

    async def _add_related_documents(
        self,
        enhanced_results: List[EnhancedSearchResult],
        document_graph: Dict[str, DocumentNode],
        max_related_per_result: int,
    ) -> None:
        """Add related documents to each result"""

        for result in enhanced_results:
            if not result.document_node:
                continue

            related_docs = []

            # Get related documents from graph
            for relation in result.document_node.relations[:max_related_per_result]:
                if relation.target_doc_id in document_graph:
                    target_node = document_graph[relation.target_doc_id]

                    related_doc = {
                        "doc_id": target_node.doc_id,
                        "title": target_node.title,
                        "content": (
                            target_node.content[:200] + "..."
                            if len(target_node.content) > 200
                            else target_node.content
                        ),
                        "relation_type": relation.relation_type,
                        "relation_strength": relation.strength,
                        "relation_evidence": relation.evidence,
                        "document_type": target_node.document_type,
                        "importance_score": target_node.importance_score,
                    }
                    related_docs.append(related_doc)

            result.related_documents = related_docs

    def _convert_to_enhanced_result(
        self, base_result: SearchResult
    ) -> EnhancedSearchResult:
        """Convert basic search result to enhanced result (fallback)"""
        return EnhancedSearchResult(
            doc_id=base_result.doc_id,
            title=base_result.title,
            content=base_result.content,
            score=base_result.score,
            source=base_result.source,
            source_type=base_result.source_type,
            url=base_result.url,
            author=base_result.author,
            created_at=base_result.created_at,
            tags=base_result.tags,
            collection_name=base_result.collection_name,
            chunk_index=base_result.chunk_index,
            highlights=base_result.highlights,
            contextual_score=None,
            document_node=None,
            related_documents=None,
            user_intent=None,
        )

    async def get_document_relationships(
        self, doc_id: str, max_relationships: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific document.

        Args:
            doc_id: Document ID to get relationships for
            max_relationships: Maximum number of relationships to return

        Returns:
            List of relationship data
        """
        try:
            # This would typically involve building a graph around the specific document
            # For now, return an empty list as placeholder
            logger.info(f"Getting relationships for document: {doc_id}")

            # In a full implementation, this would:
            # 1. Find the document
            # 2. Build a local graph around it
            # 3. Return relationship data

            return []

        except Exception as e:
            logger.error(f"Failed to get document relationships: {e}")
            return []

    async def analyze_search_context(
        self,
        search_history: List[str],
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze search context from user history and preferences.

        Args:
            search_history: List of previous search queries
            user_preferences: User preference data

        Returns:
            Analyzed context data for improving future searches
        """
        try:
            context_analysis = {
                "common_topics": [],
                "technical_level": "intermediate",
                "preferred_domains": [],
                "search_patterns": {},
                "recommendations": [],
            }

            if not search_history:
                return context_analysis

            # Analyze common topics from search history
            all_words = []
            for query in search_history:
                words = query.lower().split()
                all_words.extend([word for word in words if len(word) > 3])

            # Simple frequency analysis
            from collections import Counter

            word_counts = Counter(all_words)
            context_analysis["common_topics"] = [
                word for word, count in word_counts.most_common(10)
            ]

            # Determine technical level from search terms
            advanced_terms = [
                "architecture",
                "implementation",
                "optimization",
                "scalability",
            ]
            beginner_terms = ["tutorial", "guide", "introduction", "basics"]

            advanced_count = sum(
                1
                for query in search_history
                for term in advanced_terms
                if term in query.lower()
            )
            beginner_count = sum(
                1
                for query in search_history
                for term in beginner_terms
                if term in query.lower()
            )

            if advanced_count > beginner_count:
                context_analysis["technical_level"] = "advanced"
            elif beginner_count > 0:
                context_analysis["technical_level"] = "beginner"

            # Add user preferences if available
            if user_preferences:
                context_analysis.update(user_preferences)

            logger.info(
                f"Analyzed search context: {context_analysis['technical_level']} level, {len(context_analysis['common_topics'])} common topics"
            )

            return context_analysis

        except Exception as e:
            logger.error(f"Failed to analyze search context: {e}")
            return {"error": str(e)}

    async def get_search_suggestions(
        self,
        partial_query: str,
        user_context: Optional[Dict[str, Any]] = None,
        max_suggestions: int = 5,
    ) -> List[str]:
        """
        Get intelligent search suggestions based on partial query and user context.

        Args:
            partial_query: Partial search query
            user_context: User context for personalization
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested search queries
        """
        try:
            suggestions = []

            # Simple suggestion logic (can be enhanced with ML)
            query_lower = partial_query.lower()

            # Common completions based on patterns
            suggestion_patterns = {
                "how to": ["implement", "configure", "setup", "deploy", "debug"],
                "docker": ["container", "compose", "build", "deployment", "networking"],
                "api": ["design", "documentation", "testing", "security", "versioning"],
                "database": [
                    "design",
                    "optimization",
                    "migration",
                    "backup",
                    "indexing",
                ],
                "python": [
                    "best practices",
                    "frameworks",
                    "testing",
                    "deployment",
                    "performance",
                ],
            }

            for pattern, completions in suggestion_patterns.items():
                if pattern in query_lower:
                    for completion in completions:
                        suggestion = f"{partial_query} {completion}"
                        suggestions.append(suggestion)
                        if len(suggestions) >= max_suggestions:
                            break
                    break

            # Add context-based suggestions if available
            if user_context and len(suggestions) < max_suggestions:
                common_topics = user_context.get("common_topics", [])
                for topic in common_topics[: max_suggestions - len(suggestions)]:
                    if topic not in partial_query.lower():
                        suggestions.append(f"{partial_query} {topic}")

            logger.info(
                f"Generated {len(suggestions)} suggestions for: '{partial_query}'"
            )
            return suggestions[:max_suggestions]

        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []


# Factory function to create enhanced search service
def get_enhanced_vector_search_service() -> EnhancedVectorSearchService:
    """Get an instance of the enhanced vector search service"""
    return EnhancedVectorSearchService()


# Convenience functions for backward compatibility
async def enhanced_search(
    query: str,
    collections: Optional[List[str]] = None,
    limit: int = 10,
    user_context: Optional[Dict[str, Any]] = None,
    enable_graph_analysis: bool = True,
    enable_dynamic_reranking: bool = True,
) -> List[EnhancedSearchResult]:
    """
    Convenience function for enhanced search.

    Args:
        query: Search query
        collections: Collections to search in
        limit: Maximum results
        user_context: User context for personalization
        enable_graph_analysis: Enable document graph analysis
        enable_dynamic_reranking: Enable dynamic reranking

    Returns:
        Enhanced search results
    """
    service = get_enhanced_vector_search_service()

    request = EnhancedSearchRequest(
        query=query,
        collections=collections,
        limit=limit,
        user_context=user_context,
        enable_graph_analysis=enable_graph_analysis,
        enable_dynamic_reranking=enable_dynamic_reranking,
    )

    return await service.enhanced_search(request)
