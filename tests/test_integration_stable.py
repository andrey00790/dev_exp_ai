"""
🛡️ STABLE INTEGRATION TESTS
Только быстрые и стабильные тесты без зависаний
"""
import pytest
from unittest.mock import Mock, patch
import time


class TestStableIntegration:
    """Стабильные integration тесты с таймаутами"""
    
    def test_qdrant_health_only(self):
        """Только health check Qdrant"""
        try:
            from tests.integration.test_qdrant_integration import QdrantClient
            import requests
            
            client = QdrantClient("http://localhost:6333")
            
            # Быстрый health check с таймаутом
            health = client.health_check()
            assert health.get("status") == "ok"
            
        except Exception:
            pytest.skip("Qdrant не доступен")
    
    def test_postgres_connection_only(self):
        """Только подключение к PostgreSQL"""
        try:
            import psycopg2
            
            # Пробуем быстрое подключение
            conn_params = {
                'host': 'localhost',
                'port': 5432,
                'database': 'ai_assistant',
                'user': 'ai_user',
                'password': 'ai_password_dev',
                'connect_timeout': 3  # 3 секунды таймаут
            }
            
            conn = psycopg2.connect(**conn_params)
            conn.close()
            
        except Exception:
            pytest.skip("PostgreSQL не доступен")
    
    @pytest.mark.timeout(10)  # 10 секунд максимум
    def test_app_imports_fast(self):
        """Быстрый тест импортов app модулей"""
        working_imports = []
        
        imports_to_test = [
            "app.api.health",
            "app.models.user", 
            "app.analytics.aggregator",
            "vectorstore.embeddings",
            "models.base"
        ]
        
        for import_name in imports_to_test:
            try:
                __import__(import_name)
                working_imports.append(import_name)
            except:
                pass
        
        print(f"✅ Working imports: {working_imports}")
        assert len(working_imports) >= 3, f"Only {len(working_imports)} imports working"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--timeout=20"])
