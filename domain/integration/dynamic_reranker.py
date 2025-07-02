"""
Dynamic Reranking Service - Enhanced semantic search with intelligent result reordering.
Inspired by deepwiki-open patterns for context-aware search result optimization.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from adapters.vectorstore.embeddings import get_embeddings_service
from app.core.async_utils import (AsyncTimeouts, async_retry, safe_gather,
                                  with_timeout)
from domain.integration.document_graph_builder import (DocumentGraphBuilder,
                                                       DocumentNode,
                                                       build_document_graph)
from domain.integration.search_models import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class UserIntent:
    """Analyzed user intent from query and history"""

    primary_intent: (
        str  # 'code_search', 'documentation', 'debugging', 'learning', 'implementation'
    )
    secondary_intents: List[str]
    confidence: float
    keywords: List[str]
    technical_level: str  # 'beginner', 'intermediate', 'advanced'
    domain: str  # 'frontend', 'backend', 'devops', 'data', 'general'


@dataclass
class ContextualScore:
    """Contextual scoring breakdown for transparency"""

    base_score: float
    intent_score: float
    temporal_score: float
    popularity_score: float
    relationship_score: float
    personalization_score: float
    final_score: float
    explanation: str


class DynamicReranker:
    """
    Intelligent result reranking based on user context, intent analysis, and document relationships.
    Uses machine learning patterns and heuristics to optimize search relevance.
    """

    def __init__(self):
        self.embeddings_service = get_embeddings_service()
        self.graph_builder = DocumentGraphBuilder()
        self.intent_cache = {}
        self.popularity_cache = {}

        # Intent detection patterns
        self.intent_patterns = {
            "code_search": [
                "function",
                "class",
                "method",
                "implementation",
                "code",
                "algorithm",
                "snippet",
                "example",
                "how to implement",
            ],
            "documentation": [
                "documentation",
                "guide",
                "tutorial",
                "readme",
                "docs",
                "manual",
                "reference",
                "specification",
                "how to",
            ],
            "debugging": [
                "error",
                "bug",
                "issue",
                "problem",
                "fix",
                "troubleshoot",
                "exception",
                "failure",
                "not working",
                "debug",
            ],
            "learning": [
                "learn",
                "understand",
                "explain",
                "what is",
                "introduction",
                "basics",
                "beginner",
                "tutorial",
                "overview",
            ],
            "implementation": [
                "build",
                "create",
                "develop",
                "implement",
                "setup",
                "configure",
                "deploy",
                "install",
                "architecture",
            ],
            "configuration": [
                "config",
                "settings",
                "environment",
                "setup",
                "deploy",
                "docker",
                "kubernetes",
                "env",
                "variables",
            ],
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def rerank_results(
        self,
        results: List[SearchResult],
        user_query: str,
        user_context: Optional[Dict[str, Any]] = None,
        max_results: int = None,
    ) -> List[SearchResult]:
        """
        Rerank search results based on comprehensive context analysis.

        Args:
            results: Original search results to rerank
            user_query: Original user query
            user_context: Additional user context (history, preferences, etc.)
            max_results: Maximum number of results to return

        Returns:
            Reranked list of search results with enhanced scoring
        """
        if not results:
            return results

        try:
            return await with_timeout(
                self._rerank_internal(
                    results, user_query, user_context or {}, max_results
                ),
                AsyncTimeouts.ANALYTICS_AGGREGATION,  # 60 seconds
                f"Dynamic reranking timed out with {len(results)} results",
                {
                    "results_count": len(results),
                    "query": user_query[:100],
                    "user_context_keys": (
                        list(user_context.keys()) if user_context else []
                    ),
                },
            )
        except Exception as e:
            logger.error(f"Dynamic reranking failed: {e}")
            # Return original results as fallback
            return results[:max_results] if max_results else results

    async def _rerank_internal(
        self,
        results: List[SearchResult],
        user_query: str,
        user_context: Dict[str, Any],
        max_results: Optional[int],
    ) -> List[SearchResult]:
        """Internal reranking with comprehensive analysis"""

        logger.info(f"🔄 Starting dynamic reranking for {len(results)} results...")

        # Step 1: Analyze user intent
        user_intent = await self._analyze_user_intent(user_query, user_context)
        logger.info(
            f"🎯 Detected user intent: {user_intent.primary_intent} (confidence: {user_intent.confidence:.2f})"
        )

        # Step 2: Build document graph for relationship analysis
        document_graph = None
        if len(results) > 1:
            try:
                document_graph = await build_document_graph(
                    results, include_semantic_analysis=True
                )
                logger.info(f"🔗 Built document graph with {len(document_graph)} nodes")
            except Exception as e:
                logger.warning(f"Failed to build document graph: {e}")

        # Step 3: Calculate contextual scores concurrently
        scoring_tasks = [
            self._calculate_contextual_score(
                result, user_intent, user_context, document_graph
            )
            for result in results
        ]

        contextual_scores = await safe_gather(
            *scoring_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_QUERY,
            max_concurrency=20,
        )

        # Step 4: Apply scores and rerank
        enhanced_results = []
        for i, (result, score) in enumerate(zip(results, contextual_scores)):
            if isinstance(score, ContextualScore):
                # Create enhanced result with new score
                enhanced_result = SearchResult(
                    doc_id=result.doc_id,
                    title=result.title,
                    content=result.content,
                    score=score.final_score,
                    source=result.source,
                    source_type=result.source_type,
                    url=result.url,
                    author=result.author,
                    created_at=result.created_at,
                    tags=result.tags,
                    collection_name=result.collection_name,
                    chunk_index=result.chunk_index,
                    highlights=result.highlights,
                )

                # Add contextual metadata
                enhanced_result.contextual_score = score
                enhanced_results.append(enhanced_result)
            else:
                # Keep original if scoring failed
                enhanced_results.append(result)

        # Sort by enhanced scores
        enhanced_results.sort(
            key=lambda r: getattr(
                r, "contextual_score", ContextualScore(0, 0, 0, 0, 0, 0, r.score, "")
            ).final_score,
            reverse=True,
        )

        logger.info(f"✅ Dynamic reranking completed")

        return enhanced_results[:max_results] if max_results else enhanced_results

    async def _analyze_user_intent(
        self, user_query: str, user_context: Dict[str, Any]
    ) -> UserIntent:
        """Analyze user intent from query and context"""

        cache_key = f"intent:{hash(user_query)}"
        if cache_key in self.intent_cache:
            return self.intent_cache[cache_key]

        query_lower = user_query.lower()

        # Score each intent type
        intent_scores = {}
        for intent_type, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > 0:
                intent_scores[intent_type] = score

        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[primary_intent] / len(
                self.intent_patterns[primary_intent]
            )
        else:
            primary_intent = "general"
            confidence = 0.5

        # Secondary intents
        secondary_intents = [
            intent
            for intent, score in intent_scores.items()
            if intent != primary_intent and score > 0
        ]

        # Extract keywords
        keywords = self._extract_keywords(user_query)

        # Determine technical level
        technical_level = self._determine_technical_level(user_query, user_context)

        # Determine domain
        domain = self._determine_domain(user_query, user_context)

        user_intent = UserIntent(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence=min(confidence, 1.0),
            keywords=keywords,
            technical_level=technical_level,
            domain=domain,
        )

        # Cache the result
        self.intent_cache[cache_key] = user_intent

        return user_intent

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "how",
            "what",
            "where",
            "when",
            "why",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "can",
        }

        words = query.lower().split()
        keywords = [
            word.strip(".,!?;:")
            for word in words
            if word not in stop_words and len(word) > 2
        ]

        return keywords[:10]  # Limit to top 10 keywords

    def _determine_technical_level(
        self, query: str, user_context: Dict[str, Any]
    ) -> str:
        """Determine user's technical level"""
        query_lower = query.lower()

        # Advanced indicators
        advanced_terms = [
            "implementation",
            "architecture",
            "optimization",
            "performance",
            "scalability",
            "microservices",
            "kubernetes",
            "docker",
            "algorithms",
            "complexity",
            "patterns",
            "refactoring",
        ]

        # Beginner indicators
        beginner_terms = [
            "beginner",
            "introduction",
            "basics",
            "tutorial",
            "how to",
            "getting started",
            "simple",
            "easy",
            "explain",
            "what is",
        ]

        advanced_count = sum(1 for term in advanced_terms if term in query_lower)
        beginner_count = sum(1 for term in beginner_terms if term in query_lower)

        # Use context if available
        if user_context.get("user_level"):
            return user_context["user_level"]

        if advanced_count > beginner_count:
            return "advanced"
        elif beginner_count > 0:
            return "beginner"
        else:
            return "intermediate"

    def _determine_domain(self, query: str, user_context: Dict[str, Any]) -> str:
        """Determine technical domain from query"""
        query_lower = query.lower()

        domain_keywords = {
            "frontend": [
                "react",
                "vue",
                "angular",
                "javascript",
                "css",
                "html",
                "ui",
                "component",
            ],
            "backend": [
                "api",
                "server",
                "database",
                "python",
                "java",
                "node",
                "express",
                "django",
            ],
            "devops": [
                "docker",
                "kubernetes",
                "deployment",
                "ci/cd",
                "infrastructure",
                "monitoring",
            ],
            "data": [
                "sql",
                "database",
                "analytics",
                "ml",
                "machine learning",
                "data processing",
            ],
            "mobile": ["ios", "android", "react native", "flutter", "mobile", "app"],
        }

        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        else:
            return user_context.get("preferred_domain", "general")

    async def _calculate_contextual_score(
        self,
        result: SearchResult,
        user_intent: UserIntent,
        user_context: Dict[str, Any],
        document_graph: Optional[Dict[str, DocumentNode]],
    ) -> ContextualScore:
        """Calculate comprehensive contextual score for a result"""

        base_score = result.score

        # Intent alignment score
        intent_score = await self._calculate_intent_score(result, user_intent)

        # Temporal relevance score
        temporal_score = self._calculate_temporal_score(result)

        # Popularity score (based on past interactions)
        popularity_score = await self._calculate_popularity_score(result.doc_id)

        # Relationship score (based on document graph)
        relationship_score = self._calculate_relationship_score(result, document_graph)

        # Personalization score
        personalization_score = self._calculate_personalization_score(
            result, user_context
        )

        # Weighted combination
        weights = {
            "base": 0.3,
            "intent": 0.25,
            "temporal": 0.15,
            "popularity": 0.1,
            "relationship": 0.1,
            "personalization": 0.1,
        }

        final_score = (
            base_score * weights["base"]
            + intent_score * weights["intent"]
            + temporal_score * weights["temporal"]
            + popularity_score * weights["popularity"]
            + relationship_score * weights["relationship"]
            + personalization_score * weights["personalization"]
        )

        # Create explanation
        explanation = self._create_score_explanation(
            user_intent,
            intent_score,
            temporal_score,
            popularity_score,
            relationship_score,
            personalization_score,
        )

        return ContextualScore(
            base_score=base_score,
            intent_score=intent_score,
            temporal_score=temporal_score,
            popularity_score=popularity_score,
            relationship_score=relationship_score,
            personalization_score=personalization_score,
            final_score=min(final_score, 1.0),  # Cap at 1.0
            explanation=explanation,
        )

    async def _calculate_intent_score(
        self, result: SearchResult, user_intent: UserIntent
    ) -> float:
        """Calculate how well the result matches user intent"""

        content_lower = f"{result.title} {result.content}".lower()

        # Check for intent-specific patterns
        intent_patterns = self.intent_patterns.get(user_intent.primary_intent, [])
        intent_matches = sum(
            1 for pattern in intent_patterns if pattern in content_lower
        )

        # Keyword matching
        keyword_matches = sum(
            1 for keyword in user_intent.keywords if keyword in content_lower
        )

        # Technical level alignment
        level_bonus = 0
        if user_intent.technical_level == "beginner" and any(
            term in content_lower for term in ["tutorial", "guide", "introduction"]
        ):
            level_bonus = 0.2
        elif user_intent.technical_level == "advanced" and any(
            term in content_lower
            for term in ["implementation", "architecture", "optimization"]
        ):
            level_bonus = 0.2

        # Domain alignment
        domain_bonus = 0
        if user_intent.domain != "general":
            domain_keywords = {
                "frontend": ["react", "vue", "angular", "javascript", "css"],
                "backend": ["api", "server", "database", "python", "java"],
                "devops": ["docker", "kubernetes", "deployment"],
                "data": ["sql", "database", "analytics"],
            }.get(user_intent.domain, [])

            if any(keyword in content_lower for keyword in domain_keywords):
                domain_bonus = 0.15

        # Calculate final intent score
        intent_score = (
            (intent_matches / max(len(intent_patterns), 1)) * 0.4
            + (keyword_matches / max(len(user_intent.keywords), 1)) * 0.3
            + level_bonus * 0.15
            + domain_bonus * 0.15
        )

        return min(intent_score, 1.0)

    def _calculate_temporal_score(self, result: SearchResult) -> float:
        """Calculate temporal relevance score"""

        if not result.created_at:
            return 0.5  # Neutral score for unknown dates

        try:
            # Parse created_at (assuming ISO format or timestamp)
            if isinstance(result.created_at, str):
                try:
                    created_date = datetime.fromisoformat(
                        result.created_at.replace("Z", "+00:00")
                    )
                except:
                    # Try parsing as timestamp
                    created_date = datetime.fromtimestamp(float(result.created_at))
            else:
                created_date = result.created_at

            now = (
                datetime.now(created_date.tzinfo)
                if created_date.tzinfo
                else datetime.now()
            )
            age_days = (now - created_date).days

            # Recent documents get higher scores
            if age_days <= 30:
                return 1.0  # Very recent
            elif age_days <= 90:
                return 0.8  # Recent
            elif age_days <= 365:
                return 0.6  # Somewhat recent
            elif age_days <= 730:
                return 0.4  # Older
            else:
                return 0.2  # Very old

        except Exception as e:
            logger.warning(
                f"Failed to parse created_at: {result.created_at}, error: {e}"
            )
            return 0.5

    async def _calculate_popularity_score(self, doc_id: str) -> float:
        """Calculate popularity score based on past interactions"""

        # This would typically query a database of user interactions
        # For now, return a placeholder value

        cache_key = f"popularity:{doc_id}"
        if cache_key in self.popularity_cache:
            return self.popularity_cache[cache_key]

        # Simulate popularity calculation
        # In a real implementation, this would query interaction logs

        # Default popularity score
        popularity_score = 0.5

        # Cache the result
        self.popularity_cache[cache_key] = popularity_score

        return popularity_score

    def _calculate_relationship_score(
        self, result: SearchResult, document_graph: Optional[Dict[str, DocumentNode]]
    ) -> float:
        """Calculate score based on document relationships"""

        if not document_graph or result.doc_id not in document_graph:
            return 0.0

        node = document_graph[result.doc_id]

        # Base relationship score
        relationship_count = len(node.relations)
        relationship_score = min(
            relationship_count * 0.1, 0.5
        )  # Max 0.5 from relationship count

        # Bonus for high-importance relationships
        strong_relationships = [r for r in node.relations if r.strength > 0.7]
        importance_bonus = min(len(strong_relationships) * 0.05, 0.2)  # Max 0.2 bonus

        # Document type bonus
        type_bonus = {
            "code": 0.1,
            "documentation": 0.05,
            "config": 0.05,
            "test": 0.0,
        }.get(node.document_type, 0.0)

        return min(relationship_score + importance_bonus + type_bonus, 1.0)

    def _calculate_personalization_score(
        self, result: SearchResult, user_context: Dict[str, Any]
    ) -> float:
        """Calculate personalization score based on user preferences"""

        # Check user preferences
        user_preferences = user_context.get("preferences", {})

        # Preferred sources
        preferred_sources = user_preferences.get("preferred_sources", [])
        if preferred_sources and result.source in preferred_sources:
            return 0.8

        # Preferred content types
        preferred_types = user_preferences.get("preferred_types", [])
        if preferred_types and result.source_type in preferred_types:
            return 0.6

        # Author preferences
        preferred_authors = user_preferences.get("preferred_authors", [])
        if preferred_authors and result.author in preferred_authors:
            return 0.7

        # Tag preferences
        preferred_tags = user_preferences.get("preferred_tags", [])
        if preferred_tags and result.tags:
            tag_matches = len(set(preferred_tags).intersection(set(result.tags)))
            if tag_matches > 0:
                return min(tag_matches * 0.2, 0.6)

        return 0.3  # Default personalization score

    def _create_score_explanation(
        self,
        user_intent: UserIntent,
        intent_score: float,
        temporal_score: float,
        popularity_score: float,
        relationship_score: float,
        personalization_score: float,
    ) -> str:
        """Create human-readable explanation of the scoring"""

        explanations = []

        if intent_score > 0.6:
            explanations.append(f"Strong match for {user_intent.primary_intent} intent")
        elif intent_score > 0.3:
            explanations.append(
                f"Moderate match for {user_intent.primary_intent} intent"
            )

        if temporal_score > 0.8:
            explanations.append("Recent content")
        elif temporal_score < 0.3:
            explanations.append("Older content")

        if popularity_score > 0.7:
            explanations.append("Popular with users")

        if relationship_score > 0.5:
            explanations.append("Well-connected in knowledge graph")

        if personalization_score > 0.6:
            explanations.append("Matches user preferences")

        return "; ".join(explanations) if explanations else "Standard relevance scoring"


# Convenience functions for external use
async def rerank_search_results(
    results: List[SearchResult],
    user_query: str,
    user_context: Optional[Dict[str, Any]] = None,
    max_results: Optional[int] = None,
) -> List[SearchResult]:
    """
    Rerank search results with dynamic contextual scoring.

    Args:
        results: Search results to rerank
        user_query: Original user query
        user_context: User context and preferences
        max_results: Maximum results to return

    Returns:
        Reranked search results
    """
    reranker = DynamicReranker()
    return await reranker.rerank_results(results, user_query, user_context, max_results)
