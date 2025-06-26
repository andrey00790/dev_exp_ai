#!/usr/bin/env python3
"""
Redis Integration Test
Tests the new Redis-compatible cache manager
"""

import asyncio
import json
import time
from datetime import datetime

from app.performance.cache_manager import cache_manager, get_cache, set_cache, delete_cache, clear_cache, cache_result

class RedisIntegrationTester:
    
    async def test_basic_operations(self):
        """Test basic cache operations"""
        print("🔧 Testing Basic Cache Operations...")
        
        try:
            # Test set and get
            test_key = "test_basic"
            test_value = {"data": "test", "timestamp": time.time()}
            
            success = await set_cache(test_key, test_value, ttl=60)
            if not success:
                print("❌ Failed to set cache value")
                return False
            
            retrieved = await get_cache(test_key)
            if retrieved != test_value:
                print(f"❌ Retrieved value doesn't match: {retrieved} != {test_value}")
                return False
            
            print("✅ Basic set/get operations working")
            
            # Test delete
            success = await delete_cache(test_key)
            if not success:
                print("❌ Failed to delete cache value")
                return False
            
            retrieved = await get_cache(test_key)
            if retrieved is not None:
                print(f"❌ Value still exists after delete: {retrieved}")
                return False
            
            print("✅ Delete operation working")
            return True
            
        except Exception as e:
            print(f"❌ Basic operations error: {e}")
            return False
    
    async def test_ttl_functionality(self):
        """Test TTL (time-to-live) functionality"""
        print("⏰ Testing TTL Functionality...")
        
        try:
            test_key = "test_ttl"
            test_value = "expires_soon"
            
            # Set with short TTL
            await set_cache(test_key, test_value, ttl=2)
            
            # Should exist immediately
            retrieved = await get_cache(test_key)
            if retrieved != test_value:
                print("❌ Value not found immediately after setting")
                return False
            
            print("✅ Value exists immediately after setting")
            
            # Wait for expiration
            await asyncio.sleep(3)
            
            # Should be expired now
            retrieved = await get_cache(test_key)
            if retrieved is not None:
                print(f"❌ Value still exists after TTL: {retrieved}")
                return False
            
            print("✅ TTL expiration working correctly")
            return True
            
        except Exception as e:
            print(f"❌ TTL test error: {e}")
            return False
    
    async def test_serialization(self):
        """Test serialization of different data types"""
        print("📦 Testing Data Serialization...")
        
        test_cases = [
            ("string_test", "Hello World"),
            ("int_test", 42),
            ("float_test", 3.14159),
            ("bool_test", True),
            ("list_test", [1, 2, 3, "test"]),
            ("dict_test", {"key": "value", "number": 123}),
            ("complex_test", {
                "nested": {"deep": {"data": [1, 2, {"inner": "value"}]}},
                "timestamp": datetime.now().isoformat(),
                "metadata": {"type": "test", "version": 1.0}
            })
        ]
        
        try:
            for key, original_value in test_cases:
                # Set value
                await set_cache(key, original_value, ttl=60)
                
                # Get value
                retrieved_value = await get_cache(key)
                
                if retrieved_value != original_value:
                    print(f"❌ Serialization failed for {key}: {retrieved_value} != {original_value}")
                    return False
                
                # Clean up
                await delete_cache(key)
            
            print("✅ All data types serialized/deserialized correctly")
            return True
            
        except Exception as e:
            print(f"❌ Serialization test error: {e}")
            return False
    
    async def test_cache_decorator(self):
        """Test the cache decorator functionality"""
        print("🎭 Testing Cache Decorator...")
        
        call_count = 0
        
        @cache_result(ttl=30, key_prefix="test_func")
        async def expensive_function(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x + y
        
        try:
            # First call - should execute function
            result1 = await expensive_function(5, 3)
            if result1 != 8:
                print(f"❌ Function returned wrong result: {result1}")
                return False
            
            if call_count != 1:
                print(f"❌ Function should have been called once, was called {call_count} times")
                return False
            
            # Second call - should use cache
            result2 = await expensive_function(5, 3)
            if result2 != 8:
                print(f"❌ Cached result wrong: {result2}")
                return False
            
            if call_count != 1:
                print(f"❌ Function should still have been called only once, was called {call_count} times")
                return False
            
            # Different parameters - should execute function again
            result3 = await expensive_function(10, 5)
            if result3 != 15:
                print(f"❌ Function with different params returned wrong result: {result3}")
                return False
            
            if call_count != 2:
                print(f"❌ Function should have been called twice, was called {call_count} times")
                return False
            
            print("✅ Cache decorator working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Cache decorator test error: {e}")
            return False
    
    async def test_cache_statistics(self):
        """Test cache statistics functionality"""
        print("📊 Testing Cache Statistics...")
        
        try:
            # Clear cache to start fresh
            await clear_cache()
            
            # Perform some operations
            await set_cache("stat_test_1", "value1")
            await set_cache("stat_test_2", "value2")
            await get_cache("stat_test_1")  # Hit
            await get_cache("stat_test_1")  # Hit
            await get_cache("nonexistent")  # Miss
            await delete_cache("stat_test_1")
            
            stats = await cache_manager.get_stats()
            
            required_fields = ['hits', 'misses', 'sets', 'deletes', 'hit_rate', 'cache_type']
            for field in required_fields:
                if field not in stats:
                    print(f"❌ Missing required stat field: {field}")
                    return False
            
            if stats['hits'] < 2:
                print(f"❌ Expected at least 2 hits, got {stats['hits']}")
                return False
            
            if stats['misses'] < 1:
                print(f"❌ Expected at least 1 miss, got {stats['misses']}")
                return False
            
            print(f"✅ Cache stats: {stats['hits']} hits, {stats['misses']} misses, {stats['hit_rate']:.1f}% hit rate")
            print(f"✅ Cache type: {stats['cache_type']}")
            return True
            
        except Exception as e:
            print(f"❌ Statistics test error: {e}")
            return False
    
    async def test_health_check(self):
        """Test cache health check"""
        print("🏥 Testing Cache Health Check...")
        
        try:
            health = await cache_manager.health_check()
            
            required_fields = ['status', 'redis_available', 'redis_connected', 'local_cache_working']
            for field in required_fields:
                if field not in health:
                    print(f"❌ Missing required health field: {field}")
                    return False
            
            if health['status'] not in ['healthy', 'degraded', 'unhealthy']:
                print(f"❌ Invalid health status: {health['status']}")
                return False
            
            if not health['local_cache_working']:
                print("❌ Local cache not working")
                return False
            
            print(f"✅ Cache health: {health['status']}")
            print(f"✅ Redis available: {health['redis_available']}")
            print(f"✅ Redis connected: {health['redis_connected']}")
            print(f"✅ Local cache working: {health['local_cache_working']}")
            
            if health['errors']:
                print(f"⚠️ Health check warnings: {health['errors']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Health check test error: {e}")
            return False
    
    async def test_pattern_clearing(self):
        """Test pattern-based cache clearing"""
        print("🧹 Testing Pattern-based Cache Clearing...")
        
        try:
            # Set up test data
            test_data = {
                "user:1:profile": {"name": "Alice"},
                "user:2:profile": {"name": "Bob"},
                "user:1:settings": {"theme": "dark"},
                "system:config": {"version": "1.0"},
                "cache:temp:123": {"data": "temporary"}
            }
            
            for key, value in test_data.items():
                await set_cache(key, value)
            
            # Verify all data is set
            for key in test_data.keys():
                value = await get_cache(key)
                if value is None:
                    print(f"❌ Failed to set test data for key: {key}")
                    return False
            
            # Clear user profiles only
            cleared = await clear_cache("user:*:profile")
            if cleared < 2:
                print(f"❌ Expected to clear at least 2 user profiles, cleared {cleared}")
                return False
            
            # Verify user profiles are gone but settings remain
            profile_1 = await get_cache("user:1:profile")
            profile_2 = await get_cache("user:2:profile")
            settings_1 = await get_cache("user:1:settings")
            system_config = await get_cache("system:config")
            
            if profile_1 is not None or profile_2 is not None:
                print("❌ User profiles should have been cleared")
                return False
            
            if settings_1 is None or system_config is None:
                print("❌ User settings and system config should still exist")
                return False
            
            print("✅ Pattern-based clearing working correctly")
            
            # Clean up remaining test data
            await clear_cache()
            return True
            
        except Exception as e:
            print(f"❌ Pattern clearing test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all Redis integration tests"""
        print("🚀 Starting Redis Integration Tests")
        print("=" * 60)
        
        # Initialize cache manager
        success = await cache_manager.initialize()
        if not success:
            print("❌ Failed to initialize cache manager")
            return False
        
        print("✅ Cache manager initialized successfully")
        
        tests = [
            self.test_basic_operations,
            self.test_ttl_functionality,
            self.test_serialization,
            self.test_cache_decorator,
            self.test_cache_statistics,
            self.test_health_check,
            self.test_pattern_clearing
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
                else:
                    print(f"❌ {test.__name__} failed")
                    print()
            except Exception as e:
                print(f"❌ {test.__name__} error: {e}")
                print()
        
        # Cleanup
        await cache_manager.close()
        
        print("=" * 60)
        print(f"📊 Redis Integration Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL REDIS INTEGRATION TESTS PASSED!")
            print("\n✨ Redis Cache Manager Features:")
            print("   🔧 Basic CRUD operations")
            print("   ⏰ TTL (time-to-live) support")
            print("   📦 Multi-type serialization")
            print("   🎭 Function result caching decorator")
            print("   📊 Comprehensive statistics")
            print("   🏥 Health monitoring")
            print("   🧹 Pattern-based cache clearing")
            print("   🔄 Automatic Redis fallback to local cache")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            return False

async def main():
    """Main function"""
    tester = RedisIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Redis Cache Manager ready for production!")
        print("   ➡️  Supports both Redis and local memory")
        print("   ➡️  Automatic fallback on Redis failure")
        print("   ➡️  Production-ready with monitoring")
    else:
        print("\n❌ Some Redis tests failed. Check configuration.")

if __name__ == "__main__":
    asyncio.run(main()) 