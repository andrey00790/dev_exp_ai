"""
Production-ready Cache Manager with Fixed Redis Compatibility
Updated for redis>=5.0 with redis.asyncio integration
"""

import asyncio
import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

# Fixed Redis imports for redis>=5.0
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        # Fallback for older versions
        import aioredis as redis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Production-ready cache manager with fixed Redis compatibility
    
    Features:
    - Redis 5.x+ compatibility with redis.asyncio
    - Intelligent fallback to memory cache
    - Automatic connection management
    - TTL configuration per cache type
    - Performance monitoring
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }
        self.is_redis_connected = False
        self.use_redis = (
            REDIS_AVAILABLE and os.getenv("USE_REDIS", "true").lower() == "true"
        )

        # TTL configurations (in seconds)
        self.ttl_config = {
            "api_response": 300,     # 5 minutes
            "search_results": 600,   # 10 minutes
            "budget_status": 60,     # 1 minute
            "llm_response": 1800,    # 30 minutes
            "user_session": 3600,    # 1 hour
            "vector_search": 900,    # 15 minutes
            "system_stats": 120,     # 2 minutes
            "default": 300,          # 5 minutes default
        }

    async def initialize(self) -> bool:
        """Initialize Redis connection with fallback"""
        if not self.use_redis:
            logger.info("🏠 Cache Manager initialized with local memory cache")
            return True

        try:
            # Create Redis client with new API
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle decoding manually
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            await self.redis_client.ping()
            self.is_redis_connected = True
            logger.info("✅ Cache Manager initialized with Redis 5.x+")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            logger.info("🔄 Falling back to local memory cache")
            self.redis_client = None
            self.is_redis_connected = False
            return True

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                await self.redis_client.aclose()
                logger.info("🔌 Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            if isinstance(value, (str, int, float, bool)):
                return json.dumps(value).encode("utf-8")
            else:
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first (for simple types)
            try:
                return json.loads(data.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle for complex objects
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise

    def _build_cache_key(self, key: str, cache_type: str) -> str:
        """Build namespaced cache key"""
        # Create hash for long keys to avoid Redis key length limits
        if len(key) > 200:
            import hashlib
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{key[:50]}...{key_hash}"

        return f"ai_assistant:{cache_type}:{key}"

    async def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._build_cache_key(key, cache_type)

        try:
            if self.is_redis_connected and self.redis_client:
                # Redis path
                data = await self.redis_client.get(cache_key)
                if data:
                    self.cache_stats["hits"] += 1
                    return self._deserialize_value(data)
                else:
                    self.cache_stats["misses"] += 1
                    return None
            else:
                # Memory cache path with TTL check
                if cache_key in self.local_cache:
                    if cache_key in self.cache_ttl:
                        if datetime.now() > self.cache_ttl[cache_key]:
                            # Expired, remove from cache
                            del self.local_cache[cache_key]
                            del self.cache_ttl[cache_key]
                            self.cache_stats["misses"] += 1
                            return None
                    self.cache_stats["hits"] += 1
                    return self.local_cache[cache_key]
                else:
                    self.cache_stats["misses"] += 1
                    return None

        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            self.cache_stats["errors"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str = "default",
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache"""
        cache_key = self._build_cache_key(key, cache_type)
        ttl_seconds = ttl or self.ttl_config.get(cache_type, self.ttl_config["default"])

        try:
            if self.is_redis_connected and self.redis_client:
                # Redis path
                serialized_value = self._serialize_value(value)
                await self.redis_client.setex(cache_key, ttl_seconds, serialized_value)
            else:
                # Memory cache path with TTL
                self.local_cache[cache_key] = value
                self.cache_ttl[cache_key] = datetime.now() + timedelta(
                    seconds=ttl_seconds
                )

            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def delete(self, key: str, cache_type: str = "default") -> bool:
        """Delete value from cache"""
        cache_key = self._build_cache_key(key, cache_type)

        try:
            if self.is_redis_connected and self.redis_client:
                # Redis path
                await self.redis_client.delete(cache_key)
            else:
                # Memory cache path
                if cache_key in self.local_cache:
                    del self.local_cache[cache_key]
                if cache_key in self.cache_ttl:
                    del self.cache_ttl[cache_key]

            self.cache_stats["deletes"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        cleared_count = 0

        try:
            if self.is_redis_connected and self.redis_client:
                # Redis pattern matching
                keys = await self.redis_client.keys(f"ai_assistant:*{pattern}*")
                if keys:
                    cleared_count = await self.redis_client.delete(*keys)
            else:
                # Memory cache pattern matching
                keys_to_delete = [
                    key for key in self.local_cache.keys() 
                    if pattern in key
                ]
                for key in keys_to_delete:
                    del self.local_cache[key]
                    if key in self.cache_ttl:
                        del self.cache_ttl[key]
                cleared_count = len(keys_to_delete)

            logger.info(
                f"Cleared {cleared_count} cache keys matching pattern: {pattern}"
            )
            return cleared_count

        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            self.cache_stats["errors"] += 1
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "cache_type": "redis" if self.is_redis_connected else "memory",
            "connected": self.is_redis_connected,
            "redis_available": REDIS_AVAILABLE,
            **self.cache_stats
        }

        try:
            if self.is_redis_connected and self.redis_client:
                # Redis stats
                info = await self.redis_client.info()
                stats.update({
                    "redis_memory_used": info.get("used_memory_human", "Unknown"),
                    "redis_keys": (
                        info.get("db0", {}).get("keys", 0) 
                        if "db0" in info else 0
                    ),
                    "redis_hits": info.get("keyspace_hits", 0),
                    "redis_misses": info.get("keyspace_misses", 0),
                })

                # Calculate hit rate
                hits = stats["redis_hits"]
                misses = stats["redis_misses"] 
                total = hits + misses
                if total > 0:
                    stats["hit_rate"] = round((hits / total) * 100, 2)
                else:
                    stats["hit_rate"] = 0
            else:
                # Memory cache stats with cleanup
                current_time = datetime.now()
                valid_keys = 0
                expired_keys = 0

                for cache_key in list(self.local_cache.keys()):
                    if cache_key in self.cache_ttl:
                        if current_time <= self.cache_ttl[cache_key]:
                            valid_keys += 1
                        else:
                            expired_keys += 1
                            # Clean up expired keys
                            del self.local_cache[cache_key]
                            del self.cache_ttl[cache_key]
                    else:
                        valid_keys += 1

                stats.update({
                    "memory_keys": valid_keys,
                    "expired_keys_cleaned": expired_keys,
                    "total_cache_entries": len(self.local_cache),
                })

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            stats["error"] = str(e)

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Health check for cache system"""
        health = {
            "status": "healthy",
            "cache_type": "redis" if self.is_redis_connected else "memory",
            "timestamp": datetime.now().isoformat()
        }

        try:
            if self.is_redis_connected and self.redis_client:
                # Test Redis connectivity
                await self.redis_client.ping()
                health["redis_ping"] = "ok"
            else:
                health["memory_cache"] = "ok"

            # Test basic operations
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": health["timestamp"]}
            
            await self.set(test_key, test_value, "system_stats", ttl=5)
            retrieved = await self.get(test_key, "system_stats")
            
            if retrieved and retrieved.get("test") is True:
                health["basic_operations"] = "ok"
                await self.delete(test_key, "system_stats")
            else:
                health["status"] = "degraded"
                health["basic_operations"] = "failed"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health


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