"""
Enhanced Semantic Search Service
Расширенный сервис семантического поиска с поддержкой множественных источников данных
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .datasource_manager import get_datasource_manager, DataSourceManager
from .datasource_interface import DataSourceInterface, DataSourceType, QueryResult
from .vector_search_service import VectorSearchService, get_vector_search_service

logger = logging.getLogger(__name__)


@dataclass
class SearchSourceConfig:
    """Конфигурация источника для поиска"""
    source_id: str
    enabled: bool = True
    weight: float = 1.0
    timeout_seconds: int = 10
    max_results: int = 100


@dataclass
class SemanticSearchConfig:
    """Конфигурация семантического поиска"""
    # Пользовательские настройки
    user_id: Optional[str] = None
    selected_sources: List[str] = field(default_factory=list)  # Выбранные пользователем источники
    
    # Настройки поиска
    limit: int = 20
    include_snippets: bool = True
    hybrid_search: bool = True
    
    # Источники для поиска
    available_sources: List[SearchSourceConfig] = field(default_factory=list)
    
    # Фильтры
    source_types: Optional[List[DataSourceType]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    # Веса для ранжирования
    source_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class SearchCandidate:
    """Кандидат результата поиска"""
    id: str
    title: str
    content: str
    source_id: str
    source_type: DataSourceType
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    snippet: Optional[str] = None


@dataclass
class SearchResult:
    """Результат семантического поиска"""
    candidates: List[SearchCandidate]
    total_results: int
    search_time_ms: float
    sources_searched: List[str]
    query: str
    search_config: SemanticSearchConfig


class EnhancedSemanticSearch:
    """
    Расширенный семантический поиск с поддержкой множественных источников
    
    Возможности:
    - Параллельный поиск по выбранным источникам
    - Интеллектуальное ранжирование результатов
    - Конфигурируемые веса источников
    - UI интеграция для выбора источников
    """
    
    def __init__(self):
        self.datasource_manager: Optional[DataSourceManager] = None
        self.vector_search: Optional[VectorSearchService] = None
        
    async def initialize(self) -> bool:
        """Инициализация сервиса"""
        try:
            logger.info("🚀 Initializing Enhanced Semantic Search...")
            
            # Инициализация менеджера источников данных
            self.datasource_manager = await get_datasource_manager()
            
            # Инициализация векторного поиска
            self.vector_search = get_vector_search_service()
            
            logger.info("✅ Enhanced Semantic Search initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enhanced Semantic Search: {e}")
            return False
    
    async def get_available_sources_for_ui(self) -> List[Dict[str, Any]]:
        """Получение списка доступных источников для UI"""
        if not self.datasource_manager:
            await self.initialize()
        
        try:
            # Получаем все доступные источники
            sources = self.datasource_manager.get_available_datasources()
            
            # Дополняем информацией для UI
            ui_sources = []
            for source in sources:
                ui_source = {
                    "id": source["source_id"],
                    "name": source["name"],
                    "type": source["source_type"],
                    "description": source.get("description", ""),
                    "enabled": source["enabled"],
                    "status": source["status"],
                    "connected": source["status"] == "connected",
                    "tables_count": source.get("tables_count", 0),
                    "schema_available": source.get("schema_available", False),
                    "tags": source.get("tags", []),
                    # UI специфичные поля
                    "selectable": True,
                    "default_enabled": source["source_id"] in self._get_default_sources(),
                    "weight": self._get_source_weight(source["source_id"])
                }
                ui_sources.append(ui_source)
            
            return ui_sources
            
        except Exception as e:
            logger.error(f"❌ Failed to get available sources: {e}")
            return []
    
    def _get_default_sources(self) -> List[str]:
        """Получение источников по умолчанию"""
        # Можно загрузить из конфигурации
        return [
            "analytics_clickhouse", 
            "production_ydb",
            "confluence_main",
            "gitlab_main"
        ]
    
    def _get_source_weight(self, source_id: str) -> float:
        """Получение веса источника"""
        # Веса по умолчанию
        default_weights = {
            "clickhouse": 1.0,
            "ydb": 0.9,
            "confluence": 1.2,
            "gitlab": 0.8,
            "jira": 0.6,
            "local_files": 1.1
        }
        
        # Попытка определить тип по source_id
        for type_name, weight in default_weights.items():
            if type_name in source_id.lower():
                return weight
        
        return 1.0  # Вес по умолчанию
    
    async def search(self, query: str, config: SemanticSearchConfig) -> SearchResult:
        """
        Выполнение семантического поиска
        
        Args:
            query: Поисковый запрос
            config: Конфигурация поиска
            
        Returns:
            Результаты поиска
        """
        start_time = time.time()
        
        try:
            # Определяем источники для поиска
            sources_to_search = await self._determine_search_sources(config)
            
            if not sources_to_search:
                logger.warning("No sources available for search")
                return SearchResult(
                    candidates=[],
                    total_results=0,
                    search_time_ms=0.0,
                    sources_searched=[],
                    query=query,
                    search_config=config
                )
            
            # Этап 1: Сбор кандидатов из всех источников параллельно
            candidates = await self._collect_candidates(query, sources_to_search, config)
            
            # Этап 2: Общее ранжирование результатов
            ranked_candidates = await self._rank_results(query, candidates, config)
            
            # Ограничиваем количество результатов
            final_candidates = ranked_candidates[:config.limit]
            
            search_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Search completed: {len(final_candidates)} results in {search_time:.2f}ms")
            
            return SearchResult(
                candidates=final_candidates,
                total_results=len(candidates),
                search_time_ms=search_time,
                sources_searched=[s.config.source_id for s in sources_to_search],
                query=query,
                search_config=config
            )
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            search_time = (time.time() - start_time) * 1000
            
            return SearchResult(
                candidates=[],
                total_results=0,
                search_time_ms=search_time,
                sources_searched=[],
                query=query,
                search_config=config
            )
    
    async def _determine_search_sources(self, config: SemanticSearchConfig) -> List[DataSourceInterface]:
        """Определение источников для поиска"""
        if not self.datasource_manager:
            return []
        
        # Если пользователь не указал источники, используем все доступные
        if not config.selected_sources:
            config.selected_sources = self._get_default_sources()
        
        # Получаем все доступные источники
        all_sources = await self.datasource_manager.get_enabled_datasources(config.source_types)
        
        # Фильтруем по выбранным пользователем
        selected_sources = []
        for source in all_sources:
            if source.config.source_id in config.selected_sources:
                selected_sources.append(source)
        
        return selected_sources
    
    async def _collect_candidates(
        self, 
        query: str, 
        sources: List[DataSourceInterface], 
        config: SemanticSearchConfig
    ) -> List[SearchCandidate]:
        """Сбор кандидатов из всех источников параллельно"""
        
        async def search_single_source(source: DataSourceInterface) -> List[SearchCandidate]:
            """Поиск в одном источнике"""
            try:
                candidates = []
                
                # Для SQL источников используем полнотекстовый поиск
                if source.config.source_type in [DataSourceType.CLICKHOUSE, DataSourceType.YDB]:
                    candidates.extend(await self._search_sql_source(query, source, config))
                
                # Дополнительно используем векторный поиск если доступен
                if self.vector_search and config.hybrid_search:
                    vector_candidates = await self._search_vector_source(query, source, config)
                    candidates.extend(vector_candidates)
                
                return candidates
                
            except Exception as e:
                logger.error(f"❌ Search failed for source {source.config.source_id}: {e}")
                return []
        
        # Запускаем поиск по всем источникам параллельно
        tasks = [search_single_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Собираем все кандидаты
        all_candidates = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Source {sources[i].config.source_id} search failed: {result}")
            elif isinstance(result, list):
                all_candidates.extend(result)
        
        return all_candidates
    
    async def _search_sql_source(
        self, 
        query: str, 
        source: DataSourceInterface, 
        config: SemanticSearchConfig
    ) -> List[SearchCandidate]:
        """Поиск в SQL источнике данных"""
        try:
            # Базовый полнотекстовый поиск
            # В реальной реализации здесь будет более сложная логика
            search_query = f"""
            SELECT 
                id,
                title,
                content,
                score,
                metadata
            FROM documents 
            WHERE content ILIKE '%{query}%' 
               OR title ILIKE '%{query}%'
            LIMIT {config.limit}
            """
            
            result = await source.query(search_query)
            
            candidates = []
            for row in result.data:
                candidate = SearchCandidate(
                    id=str(row.get("id", "")),
                    title=row.get("title", ""),
                    content=row.get("content", ""),
                    source_id=source.config.source_id,
                    source_type=source.config.source_type,
                    score=float(row.get("score", 0.5)),
                    metadata=row.get("metadata", {}),
                    snippet=row.get("content", "")[:200] + "..." if config.include_snippets else None
                )
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"❌ SQL search failed for {source.config.source_id}: {e}")
            return []
    
    async def _search_vector_source(
        self, 
        query: str, 
        source: DataSourceInterface, 
        config: SemanticSearchConfig
    ) -> List[SearchCandidate]:
        """Поиск в векторном индексе"""
        try:
            if not self.vector_search:
                return []
            
            # Векторный поиск через существующий сервис
            from .vector_search_service import SearchRequest
            
            search_request = SearchRequest(
                query=query,
                collections=[source.config.source_id],
                limit=config.limit,
                include_snippets=config.include_snippets,
                hybrid_search=True
            )
            
            vector_results = await self.vector_search.search(search_request)
            
            candidates = []
            for result in vector_results:
                candidate = SearchCandidate(
                    id=result.id,
                    title=result.title,
                    content=result.content,
                    source_id=source.config.source_id,
                    source_type=source.config.source_type,
                    score=result.score,
                    metadata=result.metadata,
                    snippet=result.snippet
                )
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Vector search failed for {source.config.source_id}: {e}")
            return []
    
    async def _rank_results(
        self, 
        query: str, 
        candidates: List[SearchCandidate], 
        config: SemanticSearchConfig
    ) -> List[SearchCandidate]:
        """Общее ранжирование результатов"""
        
        # Применяем веса источников
        for candidate in candidates:
            source_weight = config.source_weights.get(
                candidate.source_id, 
                self._get_source_weight(candidate.source_id)
            )
            candidate.score *= source_weight
        
        # Сортируем по финальному скору
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # Удаляем дубликаты по содержимому
        seen_content = set()
        unique_candidates = []
        
        for candidate in candidates:
            content_hash = hash(candidate.content[:100])  # Первые 100 символов для дедупликации
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_candidates.append(candidate)
        
        return unique_candidates


# Глобальный экземпляр
_enhanced_search: Optional[EnhancedSemanticSearch] = None


async def get_enhanced_semantic_search() -> EnhancedSemanticSearch:
    """Получение глобального экземпляра расширенного поиска"""
    global _enhanced_search
    if _enhanced_search is None:
        _enhanced_search = EnhancedSemanticSearch()
        await _enhanced_search.initialize()
    return _enhanced_search 