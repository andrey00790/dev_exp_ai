"""
Simple Cache Manager without Redis dependencies
For testing and environments where Redis is not available
"""

import json
import logging
import hashlib
from typing import Any, Optional, Dict, Union
from functools import lru_cache
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

REDIS_AVAILABLE = False

class CacheManager:
    """Simple in-memory cache manager for testing"""
    
    def __init__(self, redis_url: str = None, use_redis: bool = False):
        self._cache = {}
        self._cache_ttl = {}
        self.connected = True
        self.use_redis = False
        self.redis_client = None
        
        # Default TTL configurations (in seconds)
        self.ttl_config = {
            "api_response": 300,      # 5 minutes
            "search_results": 600,    # 10 minutes
            "budget_status": 60,      # 1 minute
            "llm_response": 1800,     # 30 minutes
            "user_session": 3600,     # 1 hour
            "vector_search": 900,     # 15 minutes
            "system_stats": 120,      # 2 minutes
            "default": 300            # 5 minutes default
        }
        
    async def initialize(self):
        """Initialize cache (no-op for simple version)"""
        logger.info("📝 Using simple in-memory cache manager")
        self.connected = True
        
    async def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._build_cache_key(key, cache_type)
        
        # Check TTL
        if cache_key in self._cache_ttl:
            if datetime.now() > self._cache_ttl[cache_key]:
                # Expired, remove from cache
                if cache_key in self._cache:
                    del self._cache[cache_key]
                del self._cache_ttl[cache_key]
                return None
        
        return self._cache.get(cache_key)
        
    async def set(self, key: str, value: Any, cache_type: str = "default", ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        cache_key = self._build_cache_key(key, cache_type)
        ttl_seconds = ttl or self.ttl_config.get(cache_type, self.ttl_config["default"])
        
        self._cache[cache_key] = value
        self._cache_ttl[cache_key] = datetime.now() + timedelta(seconds=ttl_seconds)
        return True
        
    async def delete(self, key: str, cache_type: str = "default") -> bool:
        """Delete value from cache"""
        cache_key = self._build_cache_key(key, cache_type)
        if cache_key in self._cache:
            del self._cache[cache_key]
        if cache_key in self._cache_ttl:
            del self._cache_ttl[cache_key]
        return True
        
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]
            if key in self._cache_ttl:
                del self._cache_ttl[key]
        return len(keys_to_delete)
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = datetime.now()
        valid_keys = 0
        expired_keys = 0
        
        for cache_key in list(self._cache.keys()):
            if cache_key in self._cache_ttl:
                if current_time <= self._cache_ttl[cache_key]:
                    valid_keys += 1
                else:
                    expired_keys += 1
                    # Clean up expired keys
                    del self._cache[cache_key]
                    del self._cache_ttl[cache_key]
            else:
                valid_keys += 1
        
        return {
            "cache_type": "simple_memory",
            "connected": True,
            "redis_available": False,
            "memory_keys": valid_keys,
            "expired_keys_cleaned": expired_keys,
            "total_cache_entries": len(self._cache)
        }
        
    def _build_cache_key(self, key: str, cache_type: str) -> str:
        """Build namespaced cache key"""
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{key[:50]}...{key_hash}"
        
        return f"ai_assistant:{cache_type}:{key}"
        
    async def close(self):
        """Close cache connections"""
        logger.info("Simple cache manager closed")

# Global cache manager instance
cache_manager = CacheManager()

# Simple decorator for caching
def cache_response(cache_type: str = "api_response", ttl: Optional[int] = None):
    """Simple cache decorator"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
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
    return None 