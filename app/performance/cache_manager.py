"""
Production-ready Cache Manager with Redis support and intelligent fallback
Updated with standardized async patterns
"""

import asyncio
import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.async_utils import (
    AsyncTimeouts, 
    with_timeout, 
    async_retry, 
    async_resource_manager
)
from app.core.exceptions import AsyncTimeoutError, AsyncResourceError

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Production-ready cache manager with Redis support and intelligent fallback
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Any] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        self.is_redis_connected = False
        self.use_redis = REDIS_AVAILABLE and os.getenv('USE_REDIS', 'true').lower() == 'true'
        
    async def initialize(self) -> bool:
        """Initialize Redis connection with fallback"""
        if not self.use_redis:
            logger.info("🏠 Cache Manager initialized with local memory cache")
            return True
            
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_redis_connected = True
            logger.info("✅ Cache Manager initialized with Redis")
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
                return json.dumps(value).encode('utf-8')
            else:
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    @async_retry(max_attempts=2, delay=0.1, exceptions=(redis.RedisError, AsyncTimeoutError))
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with standardized timeout and retry"""
        try:
            return await with_timeout(
                self._get_internal(key),
                AsyncTimeouts.CACHE_GET,
                f"Cache get timeout for key: {key}"
            )
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    async def _get_internal(self, key: str) -> Optional[Any]:
        """Internal get implementation"""
        if self.is_redis_connected and self.redis_client:
            # Try Redis first
            data = await self.redis_client.get(key)
            if data is not None:
                self.cache_stats['hits'] += 1
                return self._deserialize_value(data)
        
        # Fall back to local cache
        if key in self.local_cache:
            entry = self.local_cache[key]
            if isinstance(entry, dict) and 'expires_at' in entry:
                if datetime.now() > entry['expires_at']:
                    del self.local_cache[key]
                    self.cache_stats['misses'] += 1
                    return None
                self.cache_stats['hits'] += 1
                return entry['value']
            else:
                self.cache_stats['hits'] += 1
                return entry
        
        self.cache_stats['misses'] += 1
        return None
    
    @async_retry(max_attempts=2, delay=0.1, exceptions=(redis.RedisError, AsyncTimeoutError))
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with standardized timeout and retry"""
        try:
            return await with_timeout(
                self._set_internal(key, value, ttl),
                AsyncTimeouts.CACHE_SET,
                f"Cache set timeout for key: {key}"
            )
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    async def _set_internal(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Internal set implementation"""
        self.cache_stats['sets'] += 1
        
        if self.is_redis_connected and self.redis_client:
            # Set in Redis
            serialized = self._serialize_value(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)
        
        # Always set in local cache as backup
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            self.local_cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
        else:
            self.local_cache[key] = value
            
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.cache_stats['deletes'] += 1
            
            if self.is_redis_connected and self.redis_client:
                await self.redis_client.delete(key)
            
            if key in self.local_cache:
                del self.local_cache[key]
                
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.cache_stats['errors'] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.is_redis_connected and self.redis_client:
                exists = await self.redis_client.exists(key)
                if exists:
                    return True
            
            return key in self.local_cache
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries with standardized timeout"""
        try:
            return await with_timeout(
                self._clear_internal(pattern),
                AsyncTimeouts.CACHE_CLEAR,
                f"Cache clear timeout for pattern: {pattern}"
            )
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    async def _clear_internal(self, pattern: Optional[str] = None) -> int:
        """Internal clear implementation"""
        cleared = 0
        
        if self.is_redis_connected and self.redis_client:
            if pattern:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    cleared += await self.redis_client.delete(*keys)
            else:
                await self.redis_client.flushdb()
                cleared = 1
        
        # Clear local cache
        if pattern:
            import fnmatch
            keys_to_delete = [
                key for key in self.local_cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            for key in keys_to_delete:
                del self.local_cache[key]
            cleared += len(keys_to_delete)
        else:
            cleared += len(self.local_cache)
            self.local_cache.clear()
            
        logger.info(f"Cleared {cleared} cache entries")
        return cleared
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.cache_stats.copy()
        stats.update({
            'redis_connected': self.is_redis_connected,
            'redis_available': REDIS_AVAILABLE,
            'local_cache_size': len(self.local_cache),
            'cache_type': 'redis+local' if self.is_redis_connected else 'local',
            'hit_rate': (
                stats['hits'] / max(stats['hits'] + stats['misses'], 1) * 100
            )
        })
        
        if self.is_redis_connected and self.redis_client:
            try:
                info = await self.redis_client.info('memory')
                stats.update({
                    'redis_memory_used': info.get('used_memory_human', 'N/A'),
                    'redis_memory_peak': info.get('used_memory_peak_human', 'N/A'),
                    'redis_keyspace_hits': info.get('keyspace_hits', 0),
                    'redis_keyspace_misses': info.get('keyspace_misses', 0)
                })
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            'status': 'healthy',
            'redis_available': REDIS_AVAILABLE,
            'redis_connected': self.is_redis_connected,
            'local_cache_working': True,
            'errors': []
        }
        
        # Test local cache
        try:
            test_key = f"health_check_{datetime.now().timestamp()}"
            await self.set(test_key, "test_value", ttl=1)
            value = await self.get(test_key)
            if value != "test_value":
                health['local_cache_working'] = False
                health['errors'].append("Local cache test failed")
            await self.delete(test_key)
        except Exception as e:
            health['local_cache_working'] = False
            health['errors'].append(f"Local cache error: {e}")
        
        # Test Redis if connected
        if self.is_redis_connected and self.redis_client:
            try:
                await self.redis_client.ping()
                test_key = f"redis_health_{datetime.now().timestamp()}"
                await self.redis_client.set(test_key, "test", ex=1)
                value = await self.redis_client.get(test_key)
                if not value:
                    health['errors'].append("Redis connectivity test failed")
                await self.redis_client.delete(test_key)
            except Exception as e:
                health['redis_connected'] = False
                health['errors'].append(f"Redis health check failed: {e}")
        
        if health['errors']:
            health['status'] = 'degraded' if health['local_cache_working'] else 'unhealthy'
        
        return health

# Global cache manager instance
cache_manager = CacheManager()

# Convenience functions for direct use
async def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    return await cache_manager.get(key)

async def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache"""
    return await cache_manager.set(key, value, ttl)

async def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    return await cache_manager.delete(key)

async def clear_cache(pattern: Optional[str] = None) -> int:
    """Clear cache entries"""
    return await cache_manager.clear(pattern)

# Decorator for caching function results
def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await set_cache(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

async def initialize_cache() -> bool:
    """Initialize the global cache manager"""
    return await cache_manager.initialize()

async def cleanup_cache():
    """Cleanup cache connections"""
    await cache_manager.close()

# For backward compatibility
async def get_cached_result(key: str):
    """Legacy function for getting cached results"""
    return await get_cache(key)

async def cache_result_func(key: str, value: Any, ttl: int = 300):
    """Legacy function for caching results"""
    return await set_cache(key, value, ttl) 