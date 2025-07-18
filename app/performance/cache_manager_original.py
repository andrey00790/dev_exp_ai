"""
Cache Manager for AI Assistant MVP
Task 2.1.1: Redis Caching Layer Implementation

Features:
- Redis-based distributed caching
- In-memory fallback for development
- Cache key management and TTL configuration
- Cache invalidation strategies
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Async imports with fallback
try:
    import aioredis

    REDIS_AVAILABLE = True
except (ImportError, TypeError) as e:
    # Handle both import errors and Python 3.11 compatibility issues
    logger.warning(f"Redis not available: {e}")
    aioredis = None
    aioredis = None
    REDIS_AVAILABLE = False


class CacheManager:
    """
    Comprehensive cache manager with Redis and in-memory fallback

    Supports:
    - API response caching
    - Session data caching
    - LLM response caching
    - Vector search result caching
    """

    def __init__(
        self, redis_url: str = "redis://localhost:6379", use_redis: bool = True
    ):
        self.redis_url = redis_url
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.redis_client = None
        self._memory_cache = {}
        self._cache_ttl = {}
        self.connected = False

        # Default TTL configurations (in seconds)
        self.ttl_config = {
            "api_response": 300,  # 5 minutes
            "search_results": 600,  # 10 minutes
            "budget_status": 60,  # 1 minute
            "llm_response": 1800,  # 30 minutes
            "user_session": 3600,  # 1 hour
            "vector_search": 900,  # 15 minutes
            "system_stats": 120,  # 2 minutes
            "default": 300,  # 5 minutes default
        }

    async def initialize(self):
        """Initialize cache connection"""
        if self.use_redis:
            try:
                self.redis_client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
                # Test connection
                await self.redis_client.ping()
                self.connected = True
                logger.info("✅ Redis cache manager initialized successfully")
            except Exception as e:
                logger.warning(
                    f"⚠️ Redis unavailable, falling back to memory cache: {e}"
                )
                self.use_redis = False
                self.connected = False

        if not self.use_redis:
            logger.info("📝 Using in-memory cache manager")
            self.connected = True

    async def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """Get value from cache"""
        if not self.connected:
            await self.initialize()

        cache_key = self._build_cache_key(key, cache_type)

        try:
            if self.use_redis and self.redis_client:
                value = await self.redis_client.get(cache_key)
                if value:
                    return json.loads(value)
            else:
                # Memory cache with TTL check
                if cache_key in self._memory_cache:
                    if cache_key in self._cache_ttl:
                        if datetime.now() > self._cache_ttl[cache_key]:
                            # Expired, remove from cache
                            del self._memory_cache[cache_key]
                            del self._cache_ttl[cache_key]
                            return None
                    return self._memory_cache[cache_key]

        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str = "default",
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache"""
        if not self.connected:
            await self.initialize()

        cache_key = self._build_cache_key(key, cache_type)
        ttl_seconds = ttl or self.ttl_config.get(cache_type, self.ttl_config["default"])

        try:
            if self.use_redis and self.redis_client:
                serialized_value = json.dumps(value, default=str)
                await self.redis_client.setex(cache_key, ttl_seconds, serialized_value)
            else:
                # Memory cache with TTL
                self._memory_cache[cache_key] = value
                self._cache_ttl[cache_key] = datetime.now() + timedelta(
                    seconds=ttl_seconds
                )

            return True

        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False

    async def delete(self, key: str, cache_type: str = "default") -> bool:
        """Delete value from cache"""
        cache_key = self._build_cache_key(key, cache_type)

        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.delete(cache_key)
            else:
                # Memory cache
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                if cache_key in self._cache_ttl:
                    del self._cache_ttl[cache_key]

            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        cleared_count = 0

        try:
            if self.use_redis and self.redis_client:
                keys = await self.redis_client.keys(f"ai_assistant:*{pattern}*")
                if keys:
                    cleared_count = await self.redis_client.delete(*keys)
            else:
                # Memory cache pattern matching
                keys_to_delete = [
                    key for key in self._memory_cache.keys() if pattern in key
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    if key in self._cache_ttl:
                        del self._cache_ttl[key]
                cleared_count = len(keys_to_delete)

            logger.info(
                f"Cleared {cleared_count} cache keys matching pattern: {pattern}"
            )
            return cleared_count

        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "cache_type": "redis" if self.use_redis else "memory",
            "connected": self.connected,
            "redis_available": REDIS_AVAILABLE,
        }

        try:
            if self.use_redis and self.redis_client:
                info = await self.redis_client.info()
                stats.update(
                    {
                        "redis_memory_used": info.get("used_memory_human", "Unknown"),
                        "redis_keys": (
                            info.get("db0", {}).get("keys", 0) if "db0" in info else 0
                        ),
                        "redis_hits": info.get("keyspace_hits", 0),
                        "redis_misses": info.get("keyspace_misses", 0),
                    }
                )

                # Calculate hit rate
                hits = stats["redis_hits"]
                misses = stats["redis_misses"]
                total = hits + misses
                if total > 0:
                    stats["hit_rate"] = round((hits / total) * 100, 2)
                else:
                    stats["hit_rate"] = 0
            else:
                # Memory cache stats
                current_time = datetime.now()
                valid_keys = 0
                expired_keys = 0

                for cache_key in list(self._memory_cache.keys()):
                    if cache_key in self._cache_ttl:
                        if current_time <= self._cache_ttl[cache_key]:
                            valid_keys += 1
                        else:
                            expired_keys += 1
                            # Clean up expired keys
                            del self._memory_cache[cache_key]
                            del self._cache_ttl[cache_key]
                    else:
                        valid_keys += 1

                stats.update(
                    {
                        "memory_keys": valid_keys,
                        "expired_keys_cleaned": expired_keys,
                        "total_cache_entries": len(self._memory_cache),
                    }
                )

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            stats["error"] = str(e)

        return stats

    def _build_cache_key(self, key: str, cache_type: str) -> str:
        """Build namespaced cache key"""
        # Create hash for long keys to avoid Redis key length limits
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{key[:50]}...{key_hash}"

        return f"ai_assistant:{cache_type}:{key}"

    async def close(self):
        """Close cache connections"""
        if self.use_redis and self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache connection closed")


# Global cache manager instance
cache_manager = CacheManager()


# Decorator for caching function results
def cache_response(cache_type: str = "api_response", ttl: Optional[int] = None):
    """
    Decorator to cache function responses

    Usage:
    @cache_response("search_results", ttl=600)
    async def search_documents(query: str):
        # expensive operation
        return results
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, cache_type, ttl)
            logger.debug(f"Cached result for {func.__name__}")

            return result

        return wrapper

    return decorator


# LRU cache for frequently accessed small data
@lru_cache(maxsize=1000)
def get_cached_small_data(key: str) -> Any:
    """In-memory LRU cache for small, frequently accessed data"""
    # This will be populated by calling functions
    return None
