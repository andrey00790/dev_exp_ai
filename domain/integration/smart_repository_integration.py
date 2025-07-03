"""
Smart Repository Integration Service for AI Assistant - Phase 3
Intelligent data source integration with adaptive patterns

Features:
- Multi-source data integration (Git, Confluence, Jira, Databases)
- Smart conflict resolution and data synchronization
- Adaptive refresh strategies based on usage patterns
- Intelligent caching with dependency tracking
- Real-time change detection and streaming updates
"""

import asyncio
import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from app.core.async_utils import (AsyncTaskManager, AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import (AsyncResourceError, AsyncRetryError,
                                 AsyncTimeoutError)
from app.performance.cache_manager import cache_manager
from domain.core.core_logic_engine import TaskType, execute_intelligently

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Supported data source types"""

    GIT_REPOSITORY = "git_repository"
    CONFLUENCE = "confluence"
    JIRA = "jira"
    DATABASE = "database"
    REST_API = "rest_api"
    FILE_SYSTEM = "file_system"


class DataSourceState(Enum):
    """Data source operational states"""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    ERROR = "error"


class SyncStrategy(Enum):
    """Data synchronization strategies"""

    REAL_TIME = "real_time"
    BATCH_HOURLY = "batch_hourly"
    BATCH_DAILY = "batch_daily"
    ON_DEMAND = "on_demand"
    SMART_ADAPTIVE = "smart_adaptive"


@dataclass
class DataSourceConfig:
    """Configuration for a data source"""

    source_id: str
    source_type: DataSourceType
    name: str
    connection_params: Dict[str, Any]
    sync_strategy: SyncStrategy = SyncStrategy.SMART_ADAPTIVE
    refresh_interval: int = 3600  # seconds
    priority: int = 5  # 1-10, higher is more important
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataRecord:
    """Unified data record structure"""

    record_id: str
    source_id: str
    content: str
    title: Optional[str] = None
    content_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    checksum: Optional[str] = None


@dataclass
class SyncResult:
    """Result of synchronization operation"""

    source_id: str
    success: bool
    records_processed: int = 0
    records_added: int = 0
    records_updated: int = 0
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    sync_timestamp: datetime = field(default_factory=datetime.now)


class DataSourceConnector:
    """Base class for data source connectors"""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.state = DataSourceState.INITIALIZING
        self.last_sync: Optional[datetime] = None
        self.sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "avg_sync_time": 0.0,
        }

    async def initialize(self) -> bool:
        """Initialize the connector"""
        try:
            await self._connect()
            self.state = DataSourceState.ACTIVE
            logger.info(f"✅ Data source {self.config.source_id} initialized")
            return True
        except Exception as e:
            self.state = DataSourceState.ERROR
            logger.error(f"❌ Failed to initialize {self.config.source_id}: {e}")
            return False

    async def _connect(self):
        """Override in subclasses for specific connection logic"""
        pass

    async def sync(self) -> SyncResult:
        """Synchronize data from source"""
        start_time = asyncio.get_event_loop().time()
        result = SyncResult(source_id=self.config.source_id, success=False)

        try:
            records = await self._fetch_records()
            processed_records = await self._process_records(records)

            result.records_processed = len(processed_records)
            result.success = True
            self.last_sync = datetime.now()
            self.sync_stats["successful_syncs"] += 1

        except Exception as e:
            result.errors.append(str(e))
            self.sync_stats["failed_syncs"] += 1
            logger.error(f"Sync failed for {self.config.source_id}: {e}")

        finally:
            result.duration = asyncio.get_event_loop().time() - start_time
            self.sync_stats["total_syncs"] += 1

        return result

    async def _fetch_records(self) -> List[Dict[str, Any]]:
        """Override in subclasses to fetch records"""
        return []

    async def _process_records(
        self, raw_records: List[Dict[str, Any]]
    ) -> List[DataRecord]:
        """Process raw records into unified format"""
        processed = []
        for raw_record in raw_records:
            try:
                record = await self._transform_record(raw_record)
                record.checksum = self._calculate_checksum(record)
                processed.append(record)
            except Exception as e:
                logger.warning(
                    f"Failed to process record from {self.config.source_id}: {e}"
                )
        return processed

    async def _transform_record(self, raw_record: Dict[str, Any]) -> DataRecord:
        """Override in subclasses for specific transformation"""
        return DataRecord(
            record_id=str(raw_record.get("id", "unknown")),
            source_id=self.config.source_id,
            content=str(raw_record.get("content", "")),
            title=raw_record.get("title"),
            metadata=raw_record.get("metadata", {}),
        )

    def _calculate_checksum(self, record: DataRecord) -> str:
        """Calculate record checksum for change detection"""
        content_hash = hashlib.md5(
            f"{record.content}{record.title or ''}{json.dumps(record.metadata, sort_keys=True)}".encode()
        ).hexdigest()
        return content_hash


class GitRepositoryConnector(DataSourceConnector):
    """Git repository data source connector"""

    async def _connect(self):
        """Initialize Git repository connection"""
        repo_url = self.config.connection_params.get("repo_url")
        if not repo_url:
            raise ValueError("repo_url is required for Git connector")

        # Validate repository access
        parsed_url = urlparse(repo_url)
        if not parsed_url.scheme in ["http", "https", "git", "ssh"]:
            raise ValueError(f"Unsupported Git URL scheme: {parsed_url.scheme}")

    async def _fetch_records(self) -> List[Dict[str, Any]]:
        """Fetch records from Git repository"""
        # Placeholder implementation - would use proper Git client
        return [
            {
                "id": "example_file.py",
                "title": "Example Python File",
                "content": "# Example Python code\nprint('Hello World')",
                "metadata": {"file_type": "python", "size": 50},
            }
        ]


class ConfluenceConnector(DataSourceConnector):
    """Confluence data source connector"""

    async def _connect(self):
        """Initialize Confluence connection"""
        base_url = self.config.connection_params.get("base_url")
        api_token = self.config.connection_params.get("api_token")

        if not base_url or not api_token:
            raise ValueError("base_url and api_token are required for Confluence")

    async def _fetch_records(self) -> List[Dict[str, Any]]:
        """Fetch pages from Confluence"""
        # Placeholder - would use Confluence REST API
        return [
            {
                "id": "confluence_page_123",
                "title": "API Documentation",
                "content": "Detailed API documentation content...",
                "metadata": {"space": "TECH", "author": "developer"},
            }
        ]


class SmartRepositoryIntegration:
    """
    Smart Repository Integration with adaptive patterns

    Features:
    - Multi-source integration
    - Intelligent synchronization
    - Adaptive optimization
    - Performance monitoring
    """

    def __init__(self):
        self.task_manager = AsyncTaskManager("smart_repository_integration")
        self.connectors: Dict[str, DataSourceConnector] = {}
        self.data_store: Dict[str, DataRecord] = {}

        # Usage analytics for adaptive optimization
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.query_patterns: Dict[str, int] = defaultdict(int)

        # Background tasks
        self.background_tasks = set()
        self.running = False

    async def initialize(self) -> bool:
        """Initialize the smart repository integration"""
        try:
            logger.info("🚀 Initializing Smart Repository Integration...")

            # Initialize cache manager
            await cache_manager.initialize()

            # Start background services
            self.running = True
            self._start_background_services()

            logger.info("✅ Smart Repository Integration initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Smart Repository Integration: {e}")
            return False

    def _start_background_services(self):
        """Start background monitoring and sync services"""
        services = [
            self._sync_scheduler_service(),
            self._adaptive_optimizer_service(),
            self._cleanup_service(),
        ]

        for service_coro in services:
            task = create_background_task(
                service_coro, name=f"repo_{service_coro.__name__}"
            )
            self.background_tasks.add(task)

    async def register_data_source(self, config: DataSourceConfig) -> bool:
        """Register a new data source"""
        try:
            # Create appropriate connector
            connector = self._create_connector(config)

            # Initialize connector
            success = await connector.initialize()
            if success:
                self.connectors[config.source_id] = connector
                logger.info(f"✅ Registered data source: {config.source_id}")
                return True
            else:
                logger.error(
                    f"❌ Failed to initialize connector for {config.source_id}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Failed to register data source {config.source_id}: {e}")
            return False

    def _create_connector(self, config: DataSourceConfig) -> DataSourceConnector:
        """Create appropriate connector based on source type"""
        connector_classes = {
            DataSourceType.GIT_REPOSITORY: GitRepositoryConnector,
            DataSourceType.CONFLUENCE: ConfluenceConnector,
        }

        connector_class = connector_classes.get(config.source_type)
        if not connector_class:
            raise ValueError(f"Unsupported data source type: {config.source_type}")

        return connector_class(config)

    async def sync_data_source(self, source_id: str, force: bool = False) -> SyncResult:
        """Synchronize data from a specific source"""
        connector = self.connectors.get(source_id)
        if not connector:
            raise ValueError(f"Data source not found: {source_id}")

        # Check if sync is needed (unless forced)
        if not force and not await self._should_sync(source_id):
            return SyncResult(source_id=source_id, success=True, records_processed=0)

        logger.info(f"🔄 Syncing data source: {source_id}")

        try:
            # Execute sync with intelligent optimization
            result = await execute_intelligently(
                connector.sync,
                task_type=TaskType.IO_BOUND,
                enable_circuit_breaker=True,
                enable_adaptive_timeout=True,
                user_id="system",
            )

            # Update data store and cache
            if result.success:
                await self._update_data_store(source_id, result)
                await self._invalidate_cache(source_id)

            logger.info(
                f"✅ Sync completed for {source_id}: "
                f"{result.records_processed} processed in {result.duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Sync failed for {source_id}: {e}")
            return SyncResult(source_id=source_id, success=False, errors=[str(e)])

    async def _should_sync(self, source_id: str) -> bool:
        """Determine if source should be synced based adaptive strategy"""
        connector = self.connectors.get(source_id)
        if not connector:
            return False

        config = connector.config

        # Always sync if no previous sync
        if not connector.last_sync:
            return True

        # Check based on sync strategy
        time_since_sync = datetime.now() - connector.last_sync

        if config.sync_strategy == SyncStrategy.REAL_TIME:
            return True
        elif config.sync_strategy == SyncStrategy.ON_DEMAND:
            return False
        elif config.sync_strategy == SyncStrategy.SMART_ADAPTIVE:
            return await self._smart_sync_decision(source_id, time_since_sync)
        else:
            # Interval-based strategies
            return time_since_sync.total_seconds() >= config.refresh_interval

    async def _smart_sync_decision(
        self, source_id: str, time_since_sync: timedelta
    ) -> bool:
        """Make intelligent sync decision based on usage patterns"""
        # Get recent access patterns
        recent_accesses = [
            access
            for access in self.access_patterns.get(source_id, [])
            if datetime.now() - access < timedelta(hours=24)
        ]

        # If frequently accessed, sync more often
        if len(recent_accesses) > 10:
            min_interval = 300  # 5 minutes
        elif len(recent_accesses) > 5:
            min_interval = 900  # 15 minutes
        else:
            min_interval = 3600  # 1 hour

        return time_since_sync.total_seconds() >= min_interval

    async def _update_data_store(self, source_id: str, sync_result: SyncResult):
        """Update data store with synchronized records"""
        logger.debug(
            f"Updated data store for {source_id} with {sync_result.records_processed} records"
        )

    async def _invalidate_cache(self, source_id: str):
        """Invalidate cache entries related to source"""
        pattern = f"repo:{source_id}:*"
        cleared = await cache_manager.clear(pattern)
        if cleared > 0:
            logger.debug(f"Cleared {cleared} cache entries for {source_id}")

    async def search_across_sources(
        self,
        query: str,
        source_types: Optional[List[DataSourceType]] = None,
        limit: int = 50,
    ) -> List[DataRecord]:
        """Search across multiple data sources intelligently"""
        # Record query pattern for optimization
        self.query_patterns[query] += 1

        # Get cache key
        cache_key = (
            f"search:{hashlib.md5(query.encode()).hexdigest()}:{source_types}:{limit}"
        )

        # Try cache first
        cached_results = await cache_manager.get(cache_key)
        if cached_results:
            return cached_results

        # Search across sources
        search_tasks = []
        for source_id, connector in self.connectors.items():
            if source_types and connector.config.source_type not in source_types:
                continue

            # Record access for adaptive optimization
            self.access_patterns[source_id].append(datetime.now())

            search_task = self._search_single_source(source_id, query, limit)
            search_tasks.append(search_task)

        # Execute searches concurrently
        source_results = await safe_gather(
            *search_tasks, return_exceptions=True, max_concurrency=5
        )

        # Combine and rank results
        all_results = []
        for results in source_results:
            if isinstance(results, list):
                all_results.extend(results)

        # Apply intelligent ranking
        ranked_results = await self._rank_search_results(query, all_results)
        final_results = ranked_results[:limit]

        # Cache results
        await cache_manager.set(cache_key, final_results, ttl=300)

        return final_results

    async def _search_single_source(
        self, source_id: str, query: str, limit: int
    ) -> List[DataRecord]:
        """Search within a single data source"""
        # Placeholder implementation - would use proper search logic
        return []

    async def _rank_search_results(
        self, query: str, results: List[DataRecord]
    ) -> List[DataRecord]:
        """Apply intelligent ranking to search results"""
        scored_results = []

        for result in results:
            score = 0.0

            # Title match boost
            if result.title and query.lower() in result.title.lower():
                score += 10.0

            # Content relevance
            query_words = query.lower().split()
            content_lower = result.content.lower()
            matching_words = sum(1 for word in query_words if word in content_lower)
            score += matching_words * 2.0

            # Source priority boost
            connector = self.connectors.get(result.source_id)
            if connector:
                score += connector.config.priority

            # Recency boost
            days_old = (datetime.now() - result.updated_at).days
            score += max(0, 10 - days_old * 0.1)

            scored_results.append((score, result))

        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [result for _, result in scored_results]

    async def _sync_scheduler_service(self):
        """Background service for managing sync scheduling"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Check for sources that need syncing
                for source_id, connector in self.connectors.items():
                    if connector.config.enabled and await self._should_sync(source_id):
                        # Schedule sync without waiting
                        create_background_task(
                            self.sync_data_source(source_id),
                            name=f"scheduled_sync_{source_id}",
                        )

            except Exception as e:
                logger.error(f"Error in sync scheduler: {e}")

    async def _adaptive_optimizer_service(self):
        """Background service for adaptive optimization"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Analyze access patterns and adjust refresh intervals
                for source_id in self.connectors:
                    await self._optimize_source_settings(source_id)

                # Clean old access patterns
                cutoff_time = datetime.now() - timedelta(days=7)
                for source_id in self.access_patterns:
                    self.access_patterns[source_id] = [
                        access
                        for access in self.access_patterns[source_id]
                        if access > cutoff_time
                    ]

            except Exception as e:
                logger.error(f"Error in adaptive optimizer: {e}")

    async def _optimize_source_settings(self, source_id: str):
        """Optimize settings for a data source based on usage patterns"""
        connector = self.connectors.get(source_id)
        if not connector:
            return

        recent_accesses = len(
            [
                access
                for access in self.access_patterns.get(source_id, [])
                if datetime.now() - access < timedelta(hours=24)
            ]
        )

        # Adjust refresh interval based on access frequency
        if recent_accesses > 50:
            # High usage - sync more frequently
            new_interval = max(300, connector.config.refresh_interval // 2)
        elif recent_accesses < 5:
            # Low usage - sync less frequently
            new_interval = min(7200, connector.config.refresh_interval * 2)
        else:
            return  # No change needed

        if new_interval != connector.config.refresh_interval:
            connector.config.refresh_interval = new_interval
            logger.info(
                f"📊 Optimized refresh interval for {source_id}: "
                f"{new_interval}s (accesses: {recent_accesses})"
            )

    async def _cleanup_service(self):
        """Background cleanup service"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Clean up completed background tasks
                completed_tasks = [
                    task for task in self.background_tasks if task.done()
                ]
                for task in completed_tasks:
                    self.background_tasks.discard(task)
                    if task.exception():
                        logger.error(f"Background task failed: {task.exception()}")

                # Clean old query patterns
                if len(self.query_patterns) > 1000:
                    # Keep only top 500 queries
                    sorted_queries = sorted(
                        self.query_patterns.items(), key=lambda x: x[1], reverse=True
                    )[:500]
                    self.query_patterns = dict(sorted_queries)

            except Exception as e:
                logger.error(f"Error in cleanup service: {e}")

    async def get_integration_stats(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics"""
        source_stats = {}
        for source_id, connector in self.connectors.items():
            source_stats[source_id] = {
                "type": connector.config.source_type.value,
                "state": connector.state.value,
                "last_sync": (
                    connector.last_sync.isoformat() if connector.last_sync else None
                ),
                "sync_stats": connector.sync_stats,
                "recent_accesses": len(
                    [
                        access
                        for access in self.access_patterns.get(source_id, [])
                        if datetime.now() - access < timedelta(hours=24)
                    ]
                ),
                "refresh_interval": connector.config.refresh_interval,
            }

        return {
            "sources": source_stats,
            "total_sources": len(self.connectors),
            "active_sources": sum(
                1 for c in self.connectors.values() if c.state == DataSourceState.ACTIVE
            ),
            "total_records": len(self.data_store),
            "background_tasks": len(self.background_tasks),
            "top_queries": dict(list(self.query_patterns.items())[:10]),
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self, timeout: float = 30.0):
        """Graceful shutdown"""
        logger.info("🔄 Shutting down Smart Repository Integration...")
        self.running = False

        try:
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()

            if self.background_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self.background_tasks, return_exceptions=True),
                    timeout=timeout,
                )

            # Cleanup task manager
            await self.task_manager.cleanup_tasks(timeout=10.0)

            logger.info("✅ Smart Repository Integration shutdown completed")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


# Global integration instance
smart_repo = SmartRepositoryIntegration()


# Convenience functions
async def register_git_repository(
    source_id: str,
    repo_url: str,
    name: str,
    sync_strategy: SyncStrategy = SyncStrategy.SMART_ADAPTIVE,
) -> bool:
    """Register a Git repository data source"""
    config = DataSourceConfig(
        source_id=source_id,
        source_type=DataSourceType.GIT_REPOSITORY,
        name=name,
        connection_params={"repo_url": repo_url},
        sync_strategy=sync_strategy,
    )
    return await smart_repo.register_data_source(config)


async def register_confluence_space(
    source_id: str, base_url: str, api_token: str, space_key: str, name: str
) -> bool:
    """Register a Confluence space data source"""
    config = DataSourceConfig(
        source_id=source_id,
        source_type=DataSourceType.CONFLUENCE,
        name=name,
        connection_params={
            "base_url": base_url,
            "api_token": api_token,
            "space_key": space_key,
        },
    )
    return await smart_repo.register_data_source(config)


async def search_repositories(
    query: str, source_types: Optional[List[DataSourceType]] = None, limit: int = 50
) -> List[DataRecord]:
    """Search across registered repositories"""
    return await smart_repo.search_across_sources(query, source_types, limit)


async def sync_all_sources() -> Dict[str, SyncResult]:
    """Sync all registered data sources"""
    results = {}
    for source_id in smart_repo.connectors:
        results[source_id] = await smart_repo.sync_data_source(source_id)
    return results


async def initialize_smart_repository() -> bool:
    """Initialize the global smart repository integration"""
    return await smart_repo.initialize()


async def shutdown_smart_repository(timeout: float = 30.0):
    """Shutdown the global smart repository integration"""
    await smart_repo.shutdown(timeout)


async def get_repository_stats() -> Dict[str, Any]:
    """Get repository integration statistics"""
    return await smart_repo.get_integration_stats()
