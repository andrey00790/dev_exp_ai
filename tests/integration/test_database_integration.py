#!/usr/bin/env python3
"""
Интеграционные тесты для базы данных PostgreSQL
"""

import pytest
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, Any

pytestmark = pytest.mark.integration

class TestDatabaseIntegration:
    """Интеграционные тесты базы данных"""
    
    @pytest.fixture(scope="class")
    def db_connection(self):
        """Подключение к тестовой базе данных"""
        connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'testdb'),
            'user': os.getenv('POSTGRES_USER', 'testuser'),
            'password': os.getenv('POSTGRES_PASSWORD', 'testpass')
        }
        
        try:
            conn = psycopg2.connect(**connection_params)
            conn.autocommit = True
            yield conn
        finally:
            if conn:
                conn.close()
    
    def test_database_connection(self, db_connection):
        """Тест подключения к базе данных"""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_database_schema_exists(self, db_connection):
        """Тест существования схем базы данных"""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('app_data', 'test_data')
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            assert 'app_data' in schemas
            assert 'test_data' in schemas
    
    def test_users_table_structure(self, db_connection):
        """Тест структуры таблицы пользователей"""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'app_data' AND table_name = 'users'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            expected_columns = {
                'id': 'integer',
                'username': 'character varying',
                'email': 'character varying',
                'password_hash': 'character varying',
                'is_active': 'boolean',
                'created_at': 'timestamp without time zone',
                'updated_at': 'timestamp without time zone'
            }
            
            actual_columns = {col['column_name']: col['data_type'] for col in columns}
            
            for col_name, col_type in expected_columns.items():
                assert col_name in actual_columns
                assert actual_columns[col_name] == col_type
    
    def test_user_crud_operations(self, db_connection):
        """Тест CRUD операций с пользователями"""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # CREATE
            cursor.execute("""
                INSERT INTO app_data.users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, username, email
            """, ('integration_test_user', 'integration@test.com', 'hashed_password'))
            
            created_user = cursor.fetchone()
            assert created_user['username'] == 'integration_test_user'
            assert created_user['email'] == 'integration@test.com'
            user_id = created_user['id']
            
            # READ
            cursor.execute("""
                SELECT id, username, email, is_active
                FROM app_data.users
                WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            assert user['id'] == user_id
            assert user['username'] == 'integration_test_user'
            assert user['is_active'] is True
            
            # UPDATE
            cursor.execute("""
                UPDATE app_data.users
                SET username = %s
                WHERE id = %s
                RETURNING username
            """, ('updated_test_user', user_id))
            
            updated_user = cursor.fetchone()
            assert updated_user['username'] == 'updated_test_user'
            
            # DELETE
            cursor.execute("""
                DELETE FROM app_data.users
                WHERE id = %s
                RETURNING id
            """, (user_id,))
            
            deleted_user = cursor.fetchone()
            assert deleted_user['id'] == user_id
            
            # Проверяем что пользователь удален
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM app_data.users
                WHERE id = %s
            """, (user_id,))
            
            count = cursor.fetchone()
            assert count['count'] == 0
    
    def test_user_configs_relationship(self, db_connection):
        """Тест связи пользователей и конфигураций"""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Создаем пользователя
            cursor.execute("""
                INSERT INTO app_data.users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('config_test_user', 'config@test.com', 'hashed_password'))
            
            user_id = cursor.fetchone()['id']
            
            try:
                # Создаем конфигурацию
                cursor.execute("""
                    INSERT INTO app_data.user_configs (user_id, config_type, config_name, config_data)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (user_id, 'jira', 'test_config', '{"url": "https://test.com"}'))
                
                config_id = cursor.fetchone()['id']
                
                # Проверяем связь
                cursor.execute("""
                    SELECT u.username, uc.config_type, uc.config_name, uc.config_data
                    FROM app_data.users u
                    JOIN app_data.user_configs uc ON u.id = uc.user_id
                    WHERE u.id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                assert result['username'] == 'config_test_user'
                assert result['config_type'] == 'jira'
                assert result['config_name'] == 'test_config'
                assert result['config_data']['url'] == 'https://test.com'
                
            finally:
                # Очистка
                cursor.execute("DELETE FROM app_data.users WHERE id = %s", (user_id,))
    
    def test_database_indexes(self, db_connection):
        """Тест существования индексов"""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'app_data'
                AND indexname LIKE 'idx_%'
            """)
            
            indexes = [row['indexname'] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_users_email',
                'idx_users_username',
                'idx_user_configs_user_id',
                'idx_user_configs_type',
                'idx_data_sources_user_id',
                'idx_data_sources_type'
            ]
            
            for index in expected_indexes:
                assert index in indexes, f"Индекс {index} не найден"
    
    def test_database_constraints(self, db_connection):
        """Тест ограничений базы данных"""
        with db_connection.cursor() as cursor:
            # Тест уникальности email
            cursor.execute("""
                INSERT INTO app_data.users (username, email, password_hash)
                VALUES (%s, %s, %s)
            """, ('unique_test_1', 'unique@test.com', 'password'))
            
            # Попытка вставить дублирующийся email
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO app_data.users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                """, ('unique_test_2', 'unique@test.com', 'password'))
            
            # Откатываем транзакцию
            db_connection.rollback()
    
    def test_database_performance(self, db_connection):
        """Тест производительности базы данных"""
        import time
        
        with db_connection.cursor() as cursor:
            # Тест скорости вставки
            start_time = time.time()
            
            for i in range(100):
                cursor.execute("""
                    INSERT INTO app_data.users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                """, (f'perf_user_{i}', f'perf_{i}@test.com', 'password'))
            
            insert_time = time.time() - start_time
            
            # Тест скорости поиска
            start_time = time.time()
            
            cursor.execute("""
                SELECT COUNT(*) FROM app_data.users
                WHERE email LIKE 'perf_%@test.com'
            """)
            
            search_time = time.time() - start_time
            
            # Очистка
            cursor.execute("DELETE FROM app_data.users WHERE username LIKE 'perf_user_%'")
            
            # Проверяем производительность
            assert insert_time < 5.0, f"Вставка 100 записей заняла {insert_time:.2f}s (ожидалось < 5s)"
            assert search_time < 1.0, f"Поиск занял {search_time:.2f}s (ожидалось < 1s)"


class TestDatabaseTransactions:
    """Тесты транзакций базы данных"""
    
    @pytest.fixture
    def db_connection(self):
        """Подключение к тестовой базе данных"""
        connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'testdb'),
            'user': os.getenv('POSTGRES_USER', 'testuser'),
            'password': os.getenv('POSTGRES_PASSWORD', 'testpass')
        }
        
        conn = psycopg2.connect(**connection_params)
        yield conn
        conn.close()
    
    def test_transaction_rollback(self, db_connection):
        """Тест отката транзакции"""
        with db_connection.cursor() as cursor:
            # Начинаем транзакцию
            cursor.execute("BEGIN")
            
            # Вставляем данные
            cursor.execute("""
                INSERT INTO app_data.users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('rollback_test', 'rollback@test.com', 'password'))
            
            user_id = cursor.fetchone()[0]
            
            # Проверяем что данные есть в транзакции
            cursor.execute("SELECT COUNT(*) FROM app_data.users WHERE id = %s", (user_id,))
            assert cursor.fetchone()[0] == 1
            
            # Откатываем транзакцию
            cursor.execute("ROLLBACK")
            
            # Проверяем что данные исчезли
            cursor.execute("SELECT COUNT(*) FROM app_data.users WHERE id = %s", (user_id,))
            assert cursor.fetchone()[0] == 0
    
    def test_transaction_commit(self, db_connection):
        """Тест подтверждения транзакции"""
        with db_connection.cursor() as cursor:
            # Начинаем транзакцию
            cursor.execute("BEGIN")
            
            # Вставляем данные
            cursor.execute("""
                INSERT INTO app_data.users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, ('commit_test', 'commit@test.com', 'password'))
            
            user_id = cursor.fetchone()[0]
            
            # Подтверждаем транзакцию
            cursor.execute("COMMIT")
            
            # Проверяем что данные сохранились
            cursor.execute("SELECT COUNT(*) FROM app_data.users WHERE id = %s", (user_id,))
            assert cursor.fetchone()[0] == 1
            
            # Очистка
            cursor.execute("DELETE FROM app_data.users WHERE id = %s", (user_id,))
            db_connection.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 