#!/usr/bin/env python3
"""
Интеграционные тесты для Redis
"""

import pytest
import redis
import json
import time
import os
from typing import Any, Dict

pytestmark = pytest.mark.integration

class TestRedisIntegration:
    """Интеграционные тесты Redis"""
    
    @pytest.fixture(scope="class")
    def redis_client(self):
        """Подключение к Redis"""
        try:
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=0,
                decode_responses=True,
                socket_timeout=5,  # Таймаут на операции
                socket_connect_timeout=5,  # Таймаут на подключение
                health_check_interval=30,  # Проверка здоровья соединения
                retry_on_timeout=True
            )
            
            # Проверяем подключение с таймаутом
            client.ping()
            
        except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
            pytest.skip(f"Redis не доступен: {e}")
        
        yield client
        
        # Очистка после тестов
        try:
            client.flushdb()
            client.close()
        except Exception:
            pass  # Игнорируем ошибки при закрытии
    
    @pytest.mark.timeout(10)  # Таймаут на весь тест
    def test_redis_connection(self, redis_client):
        """Тест подключения к Redis"""
        try:
            response = redis_client.ping()
            assert response is True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            pytest.skip(f"Redis connection failed: {e}")
    
    @pytest.mark.timeout(15)
    def test_redis_basic_operations(self, redis_client):
        """Тест базовых операций Redis"""
        try:
            # SET/GET
            redis_client.set('test_key', 'test_value')
            value = redis_client.get('test_key')
            assert value == 'test_value'
            
            # EXISTS
            assert redis_client.exists('test_key') == 1
            assert redis_client.exists('nonexistent_key') == 0
            
            # DELETE
            redis_client.delete('test_key')
            assert redis_client.exists('test_key') == 0
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            pytest.skip(f"Redis operation failed: {e}")
    
    @pytest.mark.timeout(20)
    def test_redis_expiration(self, redis_client):
        """Тест истечения срока действия ключей"""
        try:
            # Устанавливаем ключ с TTL
            redis_client.setex('expiring_key', 2, 'expiring_value')
            
            # Проверяем что ключ существует
            assert redis_client.get('expiring_key') == 'expiring_value'
            
            # Проверяем TTL
            ttl = redis_client.ttl('expiring_key')
            assert 0 < ttl <= 2
            
            # Ждем истечения
            time.sleep(3)
            
            # Проверяем что ключ исчез
            assert redis_client.get('expiring_key') is None
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            pytest.skip(f"Redis expiration test failed: {e}")
    
    @pytest.mark.timeout(15)
    def test_redis_json_operations(self, redis_client):
        """Тест операций с JSON данными"""
        try:
            test_data = {
                'user_id': 123,
                'username': 'test_user',
                'preferences': {
                    'theme': 'dark',
                    'language': 'en'
                },
                'last_login': '2024-01-01T00:00:00Z'
            }
            
            # Сохраняем JSON
            redis_client.set('user:123', json.dumps(test_data))
            
            # Получаем и парсим JSON
            stored_data = json.loads(redis_client.get('user:123'))
            
            assert stored_data == test_data
            assert stored_data['user_id'] == 123
            assert stored_data['preferences']['theme'] == 'dark'
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            pytest.skip(f"Redis JSON test failed: {e}")
    
    @pytest.mark.timeout(15)
    def test_redis_hash_operations(self, redis_client):
        """Тест операций с хешами"""
        try:
            hash_key = 'user:456'
            
            # HSET
            redis_client.hset(hash_key, mapping={
                'username': 'hash_user',
                'email': 'hash@test.com',
                'active': 'true'
            })
            
            # HGET
            username = redis_client.hget(hash_key, 'username')
            assert username == 'hash_user'
            
            # HGETALL
            user_data = redis_client.hgetall(hash_key)
            assert user_data['username'] == 'hash_user'
            assert user_data['email'] == 'hash@test.com'
            assert user_data['active'] == 'true'
            
            # HEXISTS
            assert redis_client.hexists(hash_key, 'username') is True
            assert redis_client.hexists(hash_key, 'nonexistent') is False
            
            # HDEL
            redis_client.hdel(hash_key, 'active')
            assert redis_client.hexists(hash_key, 'active') is False
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            pytest.skip(f"Redis hash test failed: {e}")
    
    def test_redis_list_operations(self, redis_client):
        """Тест операций со списками"""
        list_key = 'recent_searches'
        
        # LPUSH
        redis_client.lpush(list_key, 'search1', 'search2', 'search3')
        
        # LLEN
        length = redis_client.llen(list_key)
        assert length == 3
        
        # LRANGE
        searches = redis_client.lrange(list_key, 0, -1)
        assert searches == ['search3', 'search2', 'search1']  # LIFO порядок
        
        # LPOP
        latest_search = redis_client.lpop(list_key)
        assert latest_search == 'search3'
        
        # Проверяем что длина уменьшилась
        assert redis_client.llen(list_key) == 2
    
    def test_redis_set_operations(self, redis_client):
        """Тест операций с множествами"""
        set_key = 'user_tags'
        
        # SADD
        redis_client.sadd(set_key, 'python', 'redis', 'testing', 'integration')
        
        # SCARD
        count = redis_client.scard(set_key)
        assert count == 4
        
        # SISMEMBER
        assert redis_client.sismember(set_key, 'python') == 1
        assert redis_client.sismember(set_key, 'java') == 0
        
        # SMEMBERS
        members = redis_client.smembers(set_key)
        assert 'python' in members
        assert 'redis' in members
        assert len(members) == 4
        
        # SREM
        redis_client.srem(set_key, 'testing')
        assert redis_client.sismember(set_key, 'testing') == 0
        assert redis_client.scard(set_key) == 3
    
    def test_redis_sorted_set_operations(self, redis_client):
        """Тест операций с отсортированными множествами"""
        zset_key = 'user_scores'
        
        # ZADD
        redis_client.zadd(zset_key, {
            'user1': 100,
            'user2': 200,
            'user3': 150,
            'user4': 300
        })
        
        # ZCARD
        count = redis_client.zcard(zset_key)
        assert count == 4
        
        # ZSCORE
        score = redis_client.zscore(zset_key, 'user2')
        assert score == 200.0
        
        # ZRANGE (по возрастанию)
        ascending = redis_client.zrange(zset_key, 0, -1)
        assert ascending == ['user1', 'user3', 'user2', 'user4']
        
        # ZREVRANGE (по убыванию)
        descending = redis_client.zrevrange(zset_key, 0, -1)
        assert descending == ['user4', 'user2', 'user3', 'user1']
        
        # ZRANGEBYSCORE
        mid_scores = redis_client.zrangebyscore(zset_key, 150, 250)
        assert 'user3' in mid_scores
        assert 'user2' in mid_scores
        assert len(mid_scores) == 2
    
    def test_redis_pipeline(self, redis_client):
        """Тест пайплайна Redis"""
        pipe = redis_client.pipeline()
        
        # Добавляем команды в пайплайн
        pipe.set('pipe_key1', 'value1')
        pipe.set('pipe_key2', 'value2')
        pipe.get('pipe_key1')
        pipe.get('pipe_key2')
        pipe.delete('pipe_key1', 'pipe_key2')
        
        # Выполняем пайплайн
        results = pipe.execute()
        
        # Проверяем результаты
        assert results[0] is True  # SET pipe_key1
        assert results[1] is True  # SET pipe_key2
        assert results[2] == 'value1'  # GET pipe_key1
        assert results[3] == 'value2'  # GET pipe_key2
        assert results[4] == 2  # DELETE (количество удаленных ключей)
    
    def test_redis_pub_sub(self, redis_client):
        """Тест Pub/Sub функциональности"""
        # Создаем отдельное подключение для подписки
        subscriber = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=0,
            decode_responses=True
        )
        
        try:
            # Подписываемся на канал
            pubsub = subscriber.pubsub()
            pubsub.subscribe('test_channel')
            
            # Пропускаем сообщение о подписке
            message = pubsub.get_message(timeout=1)
            assert message['type'] == 'subscribe'
            
            # Публикуем сообщение
            redis_client.publish('test_channel', 'test_message')
            
            # Получаем сообщение
            message = pubsub.get_message(timeout=1)
            assert message is not None
            assert message['type'] == 'message'
            assert message['data'] == 'test_message'
            
        finally:
            pubsub.close()
            subscriber.close()
    
    def test_redis_performance(self, redis_client):
        """Тест производительности Redis"""
        import time
        
        # Тест скорости записи
        start_time = time.time()
        
        for i in range(1000):
            redis_client.set(f'perf_key_{i}', f'value_{i}')
        
        write_time = time.time() - start_time
        
        # Тест скорости чтения
        start_time = time.time()
        
        for i in range(1000):
            redis_client.get(f'perf_key_{i}')
        
        read_time = time.time() - start_time
        
        # Очистка
        keys = [f'perf_key_{i}' for i in range(1000)]
        redis_client.delete(*keys)
        
        # Проверяем производительность
        assert write_time < 2.0, f"Запись 1000 ключей заняла {write_time:.2f}s (ожидалось < 2s)"
        assert read_time < 1.0, f"Чтение 1000 ключей заняло {read_time:.2f}s (ожидалось < 1s)"
    
    def test_redis_memory_usage(self, redis_client):
        """Тест использования памяти"""
        # Получаем информацию о памяти
        info = redis_client.info('memory')
        
        # Проверяем что Redis использует разумное количество памяти
        used_memory = info['used_memory']
        used_memory_mb = used_memory / (1024 * 1024)
        
        # Для тестового окружения ожидаем < 100MB
        assert used_memory_mb < 100, f"Redis использует {used_memory_mb:.2f}MB памяти (ожидалось < 100MB)"
        
        # Проверяем что есть информация о пике памяти
        assert 'used_memory_peak' in info
        assert info['used_memory_peak'] >= used_memory


class TestRedisCaching:
    """Тесты кэширования в Redis"""
    
    @pytest.fixture
    def redis_client(self):
        """Подключение к Redis для тестов кэширования"""
        client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=1,  # Используем другую БД
            decode_responses=True
        )
        
        client.ping()
        yield client
        
        client.flushdb()
        client.close()
    
    def test_cache_user_session(self, redis_client):
        """Тест кэширования пользовательской сессии"""
        session_id = 'session_123'
        session_data = {
            'user_id': 456,
            'username': 'cached_user',
            'login_time': '2024-01-01T12:00:00Z',
            'permissions': ['read', 'write']
        }
        
        # Кэшируем сессию на 1 час
        redis_client.setex(
            f'session:{session_id}',
            3600,
            json.dumps(session_data)
        )
        
        # Получаем из кэша
        cached_session = redis_client.get(f'session:{session_id}')
        assert cached_session is not None
        
        parsed_session = json.loads(cached_session)
        assert parsed_session['user_id'] == 456
        assert parsed_session['username'] == 'cached_user'
        assert 'read' in parsed_session['permissions']
    
    def test_cache_search_results(self, redis_client):
        """Тест кэширования результатов поиска"""
        search_query = 'integration testing'
        search_results = [
            {'id': 1, 'title': 'Integration Testing Guide', 'score': 0.95},
            {'id': 2, 'title': 'Testing Best Practices', 'score': 0.87},
            {'id': 3, 'title': 'Redis Integration', 'score': 0.82}
        ]
        
        # Кэшируем результаты поиска на 30 минут
        cache_key = f'search:{hash(search_query)}'
        redis_client.setex(
            cache_key,
            1800,
            json.dumps(search_results)
        )
        
        # Получаем из кэша
        cached_results = redis_client.get(cache_key)
        assert cached_results is not None
        
        parsed_results = json.loads(cached_results)
        assert len(parsed_results) == 3
        assert parsed_results[0]['title'] == 'Integration Testing Guide'
        assert parsed_results[0]['score'] == 0.95
    
    def test_cache_invalidation(self, redis_client):
        """Тест инвалидации кэша"""
        # Создаем несколько связанных ключей кэша
        redis_client.set('cache:user:123:profile', '{"name": "Test User"}')
        redis_client.set('cache:user:123:settings', '{"theme": "dark"}')
        redis_client.set('cache:user:123:permissions', '["read", "write"]')
        
        # Проверяем что все ключи существуют
        assert redis_client.exists('cache:user:123:profile') == 1
        assert redis_client.exists('cache:user:123:settings') == 1
        assert redis_client.exists('cache:user:123:permissions') == 1
        
        # Инвалидируем все ключи пользователя
        pattern = 'cache:user:123:*'
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        
        # Проверяем что все ключи удалены
        assert redis_client.exists('cache:user:123:profile') == 0
        assert redis_client.exists('cache:user:123:settings') == 0
        assert redis_client.exists('cache:user:123:permissions') == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 