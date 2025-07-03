"""
Document Graph Builder - Enhanced semantic search with document relationships.
Inspired by deepwiki-open patterns for building intelligent document networks.
"""

import ast
import asyncio
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from adapters.vectorstore.embeddings import get_embeddings_service
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError
from domain.integration.search_models import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class DocumentRelation:
    """Represents a relationship between two documents"""

    source_doc_id: str
    target_doc_id: str
    relation_type: str  # 'dependency', 'semantic', 'structural', 'temporal'
    strength: float  # 0.0 to 1.0
    evidence: List[str]  # Evidence for the relationship
    metadata: Dict[str, Any]


@dataclass
class DocumentNode:
    """Enhanced document node with relationship data"""

    doc_id: str
    title: str
    content: str
    document_type: str  # 'code', 'documentation', 'config', 'test'
    importance_score: float
    code_metadata: Dict[str, Any]
    relations: List[DocumentRelation]


class DocumentGraphBuilder:
    """
    Builds intelligent document relationship graphs for enhanced semantic search.
    Analyzes code dependencies, semantic similarities, and structural patterns.
    """

    def __init__(self):
        self.embeddings_service = get_embeddings_service()
        self.relation_cache = {}

        # Patterns for different programming languages
        self.import_patterns = {
            "python": [
                r"from\s+([^\s]+)\s+import",
                r"import\s+([^\s,]+)",
            ],
            "typescript": [
                r'import.*from\s+[\'"]([^\'\"]+)[\'"]',
                r'import\s+[\'"]([^\'\"]+)[\'"]',
            ],
            "javascript": [
                r'require\([\'"]([^\'\"]+)[\'"]\)',
                r'import.*from\s+[\'"]([^\'\"]+)[\'"]',
            ],
            "java": [
                r"import\s+([^\s;]+);",
            ],
            "go": [
                r'import\s+[\'"]([^\'\"]+)[\'"]',
            ],
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def build_document_graph(
        self, search_results: List[SearchResult], include_semantic_analysis: bool = True
    ) -> Dict[str, DocumentNode]:
        """
        Build a comprehensive document relationship graph.

        Args:
            search_results: List of search results to analyze
            include_semantic_analysis: Whether to include deep semantic analysis

        Returns:
            Dictionary mapping doc_id to DocumentNode with relationships
        """
        try:
            return await with_timeout(
                self._build_graph_internal(search_results, include_semantic_analysis),
                AsyncTimeouts.ANALYTICS_AGGREGATION,  # 60 seconds
                f"Document graph building timed out with {len(search_results)} documents",
                {"documents_count": len(search_results)},
            )
        except Exception as e:
            logger.error(f"Failed to build document graph: {e}")
            # Return basic nodes without relationships as fallback
            return {
                result.doc_id: DocumentNode(
                    doc_id=result.doc_id,
                    title=result.title,
                    content=result.content,
                    document_type=self._classify_document_type(result.content),
                    importance_score=result.score,
                    code_metadata={},
                    relations=[],
                )
                for result in search_results
            }

    async def _build_graph_internal(
        self, search_results: List[SearchResult], include_semantic_analysis: bool
    ) -> Dict[str, DocumentNode]:
        """Internal graph building with concurrent processing"""

        # Step 1: Create document nodes with parallel analysis
        logger.info(
            f"🔄 Analyzing {len(search_results)} documents for graph building..."
        )

        node_tasks = [self._create_document_node(result) for result in search_results]

        nodes = await safe_gather(
            *node_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_QUERY,
            max_concurrency=10,
        )

        # Filter out failed nodes
        valid_nodes = {
            node.doc_id: node for node in nodes if isinstance(node, DocumentNode)
        }

        logger.info(f"✅ Created {len(valid_nodes)} document nodes")

        # Step 2: Build relationships between documents
        if len(valid_nodes) > 1:
            await self._build_relationships(
                list(valid_nodes.values()), include_semantic_analysis
            )

        logger.info(f"🔗 Graph building completed with {len(valid_nodes)} nodes")
        return valid_nodes

    async def _create_document_node(self, result: SearchResult) -> DocumentNode:
        """Create enhanced document node with metadata analysis"""

        # Classify document type
        doc_type = self._classify_document_type(result.content)

        # Extract code metadata if it's a code document
        code_metadata = {}
        if doc_type == "code":
            code_metadata = await self._extract_code_metadata(
                result.content, result.source
            )

        # Calculate importance score (base score + additional factors)
        importance_score = await self._calculate_importance_score(
            result, doc_type, code_metadata
        )

        return DocumentNode(
            doc_id=result.doc_id,
            title=result.title,
            content=result.content,
            document_type=doc_type,
            importance_score=importance_score,
            code_metadata=code_metadata,
            relations=[],
        )

    def _classify_document_type(self, content: str) -> str:
        """Classify document type based on content analysis"""
        content_lower = content.lower()

        # Code files
        code_indicators = [
            "def ",
            "function ",
            "class ",
            "import ",
            "from ",
            "const ",
            "let ",
            "var ",
            "public class",
            "private ",
            "async def",
            "return ",
            "if __name__",
        ]

        # Configuration files
        config_indicators = [
            "apiVersion:",
            "kind:",
            "metadata:",
            "#!/bin/",
            "FROM ",
            "RUN ",
            "CMD ",
            "[settings]",
            "version =",
            "dependencies:",
            "scripts:",
        ]

        # Documentation
        doc_indicators = [
            "# ",
            "## ",
            "### ",
            "```",
            "README",
            "CHANGELOG",
            "Installation",
            "Usage",
            "Examples",
            "API Reference",
        ]

        # Test files
        test_indicators = [
            "test_",
            "_test",
            "describe(",
            "it(",
            "expect(",
            "assert ",
            "assertTrue",
            "setUp",
            "tearDown",
        ]

        # Count indicators
        code_count = sum(
            1 for indicator in code_indicators if indicator in content_lower
        )
        config_count = sum(
            1 for indicator in config_indicators if indicator in content_lower
        )
        doc_count = sum(1 for indicator in doc_indicators if indicator in content_lower)
        test_count = sum(
            1 for indicator in test_indicators if indicator in content_lower
        )

        # Determine type based on highest count
        counts = {
            "code": code_count,
            "config": config_count,
            "documentation": doc_count,
            "test": test_count,
        }

        return max(counts, key=counts.get) if max(counts.values()) > 0 else "unknown"

    async def _extract_code_metadata(self, content: str, source: str) -> Dict[str, Any]:
        """Extract metadata from code content"""
        metadata = {
            "language": self._detect_language(content, source),
            "imports": [],
            "functions": [],
            "classes": [],
            "complexity_score": 0,
            "dependencies": [],
        }

        try:
            # Extract imports based on detected language
            language = metadata["language"]
            if language in self.import_patterns:
                imports = set()
                for pattern in self.import_patterns[language]:
                    matches = re.findall(pattern, content)
                    imports.update(matches)
                metadata["imports"] = list(imports)

            # Extract functions and classes for Python
            if language == "python":
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            metadata["functions"].append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            metadata["classes"].append(node.name)
                except:
                    # Fallback to regex if AST parsing fails
                    metadata["functions"] = re.findall(r"def\s+(\w+)\s*\(", content)
                    metadata["classes"] = re.findall(r"class\s+(\w+)\s*[:\(]", content)

            # Simple complexity score based on cyclomatic complexity indicators
            complexity_indicators = [
                "if ",
                "elif ",
                "else:",
                "for ",
                "while ",
                "try:",
                "except:",
                "with ",
            ]
            metadata["complexity_score"] = sum(
                content.count(indicator) for indicator in complexity_indicators
            )

            # Dependencies from imports
            metadata["dependencies"] = metadata["imports"][:10]  # Limit to top 10

        except Exception as e:
            logger.warning(f"Failed to extract code metadata: {e}")

        return metadata

    def _detect_language(self, content: str, source: str) -> str:
        """Detect programming language from content and source info"""
        # File extension hints
        if any(ext in source.lower() for ext in [".py", "python"]):
            return "python"
        elif any(ext in source.lower() for ext in [".ts", ".tsx", "typescript"]):
            return "typescript"
        elif any(ext in source.lower() for ext in [".js", ".jsx", "javascript"]):
            return "javascript"
        elif any(ext in source.lower() for ext in [".java"]):
            return "java"
        elif any(ext in source.lower() for ext in [".go"]):
            return "go"

        # Content-based detection
        content_lower = content.lower()
        if "def " in content_lower and "import " in content_lower:
            return "python"
        elif "function " in content_lower and (
            "const " in content_lower or "let " in content_lower
        ):
            return (
                "typescript"
                if ": " in content and "interface " in content_lower
                else "javascript"
            )
        elif "public class" in content_lower and "import " in content_lower:
            return "java"
        elif "func " in content_lower and "package " in content_lower:
            return "go"

        return "unknown"

    async def _calculate_importance_score(
        self, result: SearchResult, doc_type: str, code_metadata: Dict[str, Any]
    ) -> float:
        """Calculate enhanced importance score"""
        base_score = result.score

        # Type-based multipliers
        type_multipliers = {
            "code": 1.2,
            "documentation": 1.0,
            "config": 1.1,
            "test": 0.8,
            "unknown": 0.9,
        }

        # Complexity bonus for code
        complexity_bonus = 0
        if doc_type == "code" and "complexity_score" in code_metadata:
            # Moderate complexity is good, too high is bad
            complexity = code_metadata["complexity_score"]
            if 5 <= complexity <= 20:
                complexity_bonus = 0.1
            elif complexity > 20:
                complexity_bonus = -0.1

        # Dependency bonus (more dependencies = more important)
        dependency_bonus = 0
        if "dependencies" in code_metadata:
            dependency_count = len(code_metadata["dependencies"])
            dependency_bonus = min(dependency_count * 0.02, 0.2)  # Max 0.2 bonus

        final_score = (
            base_score * type_multipliers.get(doc_type, 1.0)
            + complexity_bonus
            + dependency_bonus
        )
        return min(final_score, 1.0)  # Cap at 1.0

    async def _build_relationships(
        self, nodes: List[DocumentNode], include_semantic_analysis: bool
    ) -> None:
        """Build relationships between document nodes"""

        # Build dependency relationships
        await self._build_dependency_relationships(nodes)

        # Build structural relationships
        await self._build_structural_relationships(nodes)

        # Build semantic relationships (if enabled)
        if include_semantic_analysis:
            await self._build_semantic_relationships(nodes)

    async def _build_dependency_relationships(self, nodes: List[DocumentNode]) -> None:
        """Build code dependency relationships"""

        # Create mapping of potential targets
        code_nodes = [node for node in nodes if node.document_type == "code"]

        for source_node in code_nodes:
            dependencies = source_node.code_metadata.get("dependencies", [])

            for dep in dependencies:
                # Find nodes that might satisfy this dependency
                target_candidates = [
                    node
                    for node in code_nodes
                    if node.doc_id != source_node.doc_id
                    and (
                        dep in node.title.lower()
                        or dep in node.content.lower()
                        or any(
                            dep in imp for imp in node.code_metadata.get("imports", [])
                        )
                    )
                ]

                for target_node in target_candidates[:3]:  # Limit to top 3 candidates
                    relation = DocumentRelation(
                        source_doc_id=source_node.doc_id,
                        target_doc_id=target_node.doc_id,
                        relation_type="dependency",
                        strength=0.8,
                        evidence=[f"Import dependency: {dep}"],
                        metadata={"dependency_name": dep},
                    )
                    source_node.relations.append(relation)

    async def _build_structural_relationships(self, nodes: List[DocumentNode]) -> None:
        """Build structural relationships based on file/module structure"""

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i + 1 :]:
                # Check for structural similarity
                structural_score = self._calculate_structural_similarity(node1, node2)

                if structural_score > 0.3:  # Threshold for structural relationship
                    relation = DocumentRelation(
                        source_doc_id=node1.doc_id,
                        target_doc_id=node2.doc_id,
                        relation_type="structural",
                        strength=structural_score,
                        evidence=[f"Structural similarity: {structural_score:.2f}"],
                        metadata={"similarity_type": "structural"},
                    )
                    node1.relations.append(relation)

                    # Reciprocal relationship
                    reciprocal_relation = DocumentRelation(
                        source_doc_id=node2.doc_id,
                        target_doc_id=node1.doc_id,
                        relation_type="structural",
                        strength=structural_score,
                        evidence=[f"Structural similarity: {structural_score:.2f}"],
                        metadata={"similarity_type": "structural"},
                    )
                    node2.relations.append(reciprocal_relation)

    def _calculate_structural_similarity(
        self, node1: DocumentNode, node2: DocumentNode
    ) -> float:
        """Calculate structural similarity between two documents"""

        # Same document type
        type_match = 1.0 if node1.document_type == node2.document_type else 0.0

        # Common functions/classes (for code documents)
        common_elements = 0
        total_elements = 0

        if node1.document_type == "code" and node2.document_type == "code":
            functions1 = set(node1.code_metadata.get("functions", []))
            functions2 = set(node2.code_metadata.get("functions", []))
            classes1 = set(node1.code_metadata.get("classes", []))
            classes2 = set(node2.code_metadata.get("classes", []))

            common_functions = len(functions1.intersection(functions2))
            common_classes = len(classes1.intersection(classes2))

            common_elements = common_functions + common_classes
            total_elements = len(functions1.union(functions2)) + len(
                classes1.union(classes2)
            )

        element_similarity = (
            common_elements / total_elements if total_elements > 0 else 0
        )

        # Title similarity (simple)
        title_words1 = set(node1.title.lower().split())
        title_words2 = set(node2.title.lower().split())
        title_similarity = (
            len(title_words1.intersection(title_words2))
            / len(title_words1.union(title_words2))
            if title_words1.union(title_words2)
            else 0
        )

        # Weighted combination
        return type_match * 0.4 + element_similarity * 0.4 + title_similarity * 0.2

    async def _build_semantic_relationships(self, nodes: List[DocumentNode]) -> None:
        """Build semantic relationships using embeddings"""

        if len(nodes) < 2:
            return

        try:
            # Get embeddings for all documents
            texts = [
                f"{node.title} {node.content[:500]}" for node in nodes
            ]  # First 500 chars
            embeddings_results = await self.embeddings_service.embed_texts(texts)

            if not embeddings_results or len(embeddings_results) != len(nodes):
                logger.warning("Failed to get embeddings for semantic analysis")
                return

            embeddings = [result.vector for result in embeddings_results]

            # Calculate semantic similarities
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes[i + 1 :], i + 1):
                    similarity = self._cosine_similarity(embeddings[i], embeddings[j])

                    if similarity > 0.5:  # Threshold for semantic relationship
                        relation = DocumentRelation(
                            source_doc_id=node1.doc_id,
                            target_doc_id=node2.doc_id,
                            relation_type="semantic",
                            strength=similarity,
                            evidence=[f"Semantic similarity: {similarity:.2f}"],
                            metadata={"similarity_score": similarity},
                        )
                        node1.relations.append(relation)

                        # Reciprocal relationship
                        reciprocal_relation = DocumentRelation(
                            source_doc_id=node2.doc_id,
                            target_doc_id=node1.doc_id,
                            relation_type="semantic",
                            strength=similarity,
                            evidence=[f"Semantic similarity: {similarity:.2f}"],
                            metadata={"similarity_score": similarity},
                        )
                        node2.relations.append(reciprocal_relation)

        except Exception as e:
            logger.warning(f"Failed to build semantic relationships: {e}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import math

            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return dot_product / (magnitude1 * magnitude2)
        except:
            return 0.0

    def get_related_documents(
        self,
        doc_id: str,
        graph: Dict[str, DocumentNode],
        relation_types: List[str] = None,
        max_results: int = 5,
    ) -> List[Tuple[DocumentNode, DocumentRelation]]:
        """
        Get related documents for a given document ID.

        Args:
            doc_id: Source document ID
            graph: Document graph
            relation_types: Filter by relation types (optional)
            max_results: Maximum number of results

        Returns:
            List of (related_node, relation) tuples sorted by strength
        """
        if doc_id not in graph:
            return []

        source_node = graph[doc_id]
        related = []

        for relation in source_node.relations:
            if relation_types and relation.relation_type not in relation_types:
                continue

            if relation.target_doc_id in graph:
                target_node = graph[relation.target_doc_id]
                related.append((target_node, relation))

        # Sort by relationship strength
        related.sort(key=lambda x: x[1].strength, reverse=True)

        return related[:max_results]

    def get_graph_statistics(self, graph: Dict[str, DocumentNode]) -> Dict[str, Any]:
        """Get statistics about the document graph"""

        total_nodes = len(graph)
        total_relations = sum(len(node.relations) for node in graph.values())

        relation_types = defaultdict(int)
        for node in graph.values():
            for relation in node.relations:
                relation_types[relation.relation_type] += 1

        document_types = defaultdict(int)
        for node in graph.values():
            document_types[node.document_type] += 1

        avg_importance = (
            sum(node.importance_score for node in graph.values()) / total_nodes
            if total_nodes > 0
            else 0
        )

        return {
            "total_nodes": total_nodes,
            "total_relations": total_relations,
            "avg_relations_per_node": (
                total_relations / total_nodes if total_nodes > 0 else 0
            ),
            "relation_types": dict(relation_types),
            "document_types": dict(document_types),
            "average_importance_score": avg_importance,
        }


# Convenience function for external use
async def build_document_graph(
    search_results: List[SearchResult], include_semantic_analysis: bool = True
) -> Dict[str, DocumentNode]:
    """
    Build document relationship graph from search results.

    Args:
        search_results: List of search results to analyze
        include_semantic_analysis: Whether to include semantic analysis

    Returns:
        Dictionary mapping doc_id to DocumentNode with relationships
    """
    builder = DocumentGraphBuilder()
    return await builder.build_document_graph(search_results, include_semantic_analysis)
