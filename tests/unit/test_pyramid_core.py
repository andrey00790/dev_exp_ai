"""
Core Unit Tests for AI Assistant MVP
Тесты основных компонентов и бизнес-логики (база пирамиды тестирования)
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import core modules to test
try:
    from adapters.vectorstore.embeddings import EmbeddingService

    from app.security.auth import AuthService
    from app.security.hipaa_compliance import HIPAAComplianceService
    from app.services.ai_analytics_service import AIAnalyticsService
    from app.services.vector_search_service import VectorSearchService
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestVectorSearchService:
    """Unit tests for Vector Search Service"""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client"""
        mock_client = Mock()
        mock_client.search.return_value = [
            {
                "id": "doc_1",
                "score": 0.95,
                "payload": {
                    "title": "Test Document",
                    "content": "Test content for semantic search",
                    "source": "test",
                },
            }
        ]
        return mock_client

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock Embedding service"""
        mock_service = Mock()
        mock_service.embed_text.return_value = [0.1] * 1536  # OpenAI ada-002 dimensions
        return mock_service

    @pytest.fixture
    def vector_search_service(self, mock_qdrant_client, mock_embedding_service):
        """Vector search service with mocked dependencies"""
        service = VectorSearchService()
        service.qdrant_client = mock_qdrant_client
        service.embedding_service = mock_embedding_service
        return service

    def test_init_service(self, vector_search_service):
        """Test service initialization"""
        assert vector_search_service is not None
        assert hasattr(vector_search_service, "qdrant_client")
        assert hasattr(vector_search_service, "embedding_service")

    @pytest.mark.asyncio
    async def test_search_basic(self, vector_search_service):
        """Test basic semantic search functionality"""
        query = "test search query"
        results = await vector_search_service.search(query, limit=5)

        assert isinstance(results, list)
        assert len(results) > 0

        # Verify embedding was called
        vector_search_service.embedding_service.embed_text.assert_called_once_with(
            query
        )

        # Verify qdrant search was called
        vector_search_service.qdrant_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_filters(self, vector_search_service):
        """Test search with filters"""
        query = "filtered search"
        filters = {"source": "confluence", "date_range": {"from": "2024-01-01"}}

        results = await vector_search_service.search(query, filters=filters, limit=10)

        assert isinstance(results, list)

        # Verify filters were passed to qdrant
        call_args = vector_search_service.qdrant_client.search.call_args
        assert call_args is not None

    def test_validate_query_length(self, vector_search_service):
        """Test query validation"""
        # Test valid query
        assert vector_search_service._validate_query("normal query") == True

        # Test empty query
        assert vector_search_service._validate_query("") == False

        # Test very long query
        long_query = "a" * 10000
        assert vector_search_service._validate_query(long_query) == False

    def test_format_search_results(self, vector_search_service):
        """Test result formatting"""
        raw_results = [
            {
                "id": "doc_1",
                "score": 0.95,
                "payload": {
                    "title": "Test Doc",
                    "content": "Test content",
                    "source": "test",
                    "created_at": "2024-01-01T00:00:00Z",
                },
            }
        ]

        formatted = vector_search_service._format_results(raw_results)

        assert isinstance(formatted, list)
        assert len(formatted) == 1
        assert "doc_id" in formatted[0]
        assert "title" in formatted[0]
        assert "score" in formatted[0]
        assert formatted[0]["score"] == 0.95


class TestAIAnalyticsService:
    """Unit tests for AI Analytics Service"""

    @pytest.fixture
    def analytics_service(self):
        """AI Analytics service"""
        return AIAnalyticsService()

    @pytest.fixture
    def sample_usage_data(self):
        """Sample usage data for testing"""
        return [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "user_id": "user_1",
                "action": "search",
                "query": "test query",
                "results_count": 5,
                "response_time_ms": 150,
            },
            {
                "timestamp": "2024-01-01T10:05:00Z",
                "user_id": "user_2",
                "action": "rfc_generation",
                "prompt": "create notification system",
                "tokens_used": 500,
                "response_time_ms": 3000,
            },
        ]

    def test_calculate_usage_metrics(self, analytics_service, sample_usage_data):
        """Test usage metrics calculation"""
        metrics = analytics_service.calculate_usage_metrics(sample_usage_data)

        assert isinstance(metrics, dict)
        assert "total_requests" in metrics
        assert "unique_users" in metrics
        assert "average_response_time" in metrics

        assert metrics["total_requests"] == 2
        assert metrics["unique_users"] == 2
        assert metrics["average_response_time"] > 0

    def test_analyze_search_patterns(self, analytics_service):
        """Test search pattern analysis"""
        search_queries = [
            "docker deployment",
            "kubernetes config",
            "docker container",
            "api authentication",
            "docker best practices",
        ]

        patterns = analytics_service.analyze_search_patterns(search_queries)

        assert isinstance(patterns, dict)
        assert "top_terms" in patterns
        assert "docker" in patterns["top_terms"]  # Should be most frequent

    def test_generate_insights(self, analytics_service, sample_usage_data):
        """Test insights generation"""
        insights = analytics_service.generate_insights(sample_usage_data)

        assert isinstance(insights, dict)
        assert "performance_insights" in insights
        assert "usage_insights" in insights
        assert "recommendations" in insights

    def test_calculate_cost_metrics(self, analytics_service):
        """Test cost calculation for AI APIs"""
        api_usage = [
            {"provider": "openai", "model": "gpt-4", "tokens": 1000},
            {"provider": "openai", "model": "text-embedding-ada-002", "tokens": 500},
            {"provider": "anthropic", "model": "claude-3", "tokens": 800},
        ]

        costs = analytics_service.calculate_cost_metrics(api_usage)

        assert isinstance(costs, dict)
        assert "total_cost" in costs
        assert "cost_by_provider" in costs
        assert costs["total_cost"] > 0


class TestHIPAAComplianceService:
    """Unit tests for HIPAA Compliance Service"""

    @pytest.fixture
    def hipaa_service(self):
        """HIPAA compliance service"""
        return HIPAAComplianceService()

    def test_detect_phi_ssn(self, hipaa_service):
        """Test PHI detection for SSNs"""
        text_with_ssn = "Patient SSN is 123-45-6789 and DOB is 01/15/1980"

        phi_detected = hipaa_service.detect_phi(text_with_ssn)

        assert isinstance(phi_detected, list)
        assert len(phi_detected) > 0

        # Should detect SSN
        ssn_detection = next(
            (item for item in phi_detected if item["type"] == "SSN"), None
        )
        assert ssn_detection is not None
        assert ssn_detection["value"] == "123-45-6789"
        assert ssn_detection["confidence"] > 0.9

    def test_detect_phi_phone(self, hipaa_service):
        """Test PHI detection for phone numbers"""
        text_with_phone = "Contact patient at (555) 123-4567 for follow-up"

        phi_detected = hipaa_service.detect_phi(text_with_phone)

        phone_detection = next(
            (item for item in phi_detected if item["type"] == "PHONE"), None
        )
        assert phone_detection is not None
        assert "555" in phone_detection["value"]

    def test_detect_phi_email(self, hipaa_service):
        """Test PHI detection for email addresses"""
        text_with_email = "Send results to patient.name@email.com"

        phi_detected = hipaa_service.detect_phi(text_with_email)

        email_detection = next(
            (item for item in phi_detected if item["type"] == "EMAIL"), None
        )
        assert email_detection is not None
        assert "@" in email_detection["value"]

    def test_redact_phi(self, hipaa_service):
        """Test PHI redaction"""
        original_text = "Patient John Doe (SSN: 123-45-6789, Phone: 555-123-4567)"

        redacted_text = hipaa_service.redact_phi(original_text)

        assert "123-45-6789" not in redacted_text
        assert "555-123-4567" not in redacted_text
        assert "[REDACTED]" in redacted_text or "[PHI_REMOVED]" in redacted_text

    def test_audit_phi_access(self, hipaa_service):
        """Test PHI access auditing"""
        audit_entry = hipaa_service.create_audit_log(
            user_id="user_123",
            action="phi_detected",
            phi_types=["SSN", "PHONE"],
            justification="Medical records processing",
        )

        assert isinstance(audit_entry, dict)
        assert audit_entry["user_id"] == "user_123"
        assert audit_entry["action"] == "phi_detected"
        assert "timestamp" in audit_entry
        assert "audit_id" in audit_entry


class TestAuthService:
    """Unit tests for Authentication Service"""

    @pytest.fixture
    def auth_service(self):
        """Auth service with mocked dependencies"""
        service = AuthService()
        service.secret_key = "test_secret_key_for_testing"
        return service

    @pytest.fixture
    def sample_user(self):
        """Sample user data"""
        return {
            "id": "user_123",
            "email": "test@example.com",
            "username": "testuser",
            "roles": ["user"],
            "is_active": True,
        }

    def test_create_jwt_token(self, auth_service, sample_user):
        """Test JWT token creation"""
        token = auth_service.create_jwt_token(sample_user)

        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format has dots

    def test_verify_jwt_token(self, auth_service, sample_user):
        """Test JWT token verification"""
        token = auth_service.create_jwt_token(sample_user)

        decoded_user = auth_service.verify_jwt_token(token)

        assert decoded_user is not None
        assert decoded_user["email"] == sample_user["email"]
        assert decoded_user["id"] == sample_user["id"]

    def test_hash_password(self, auth_service):
        """Test password hashing"""
        password = "test_password_123"

        hashed = auth_service.hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password  # Should be hashed
        assert len(hashed) > len(password)  # Hash should be longer

    def test_verify_password(self, auth_service):
        """Test password verification"""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        # Correct password should verify
        assert auth_service.verify_password(password, hashed) == True

        # Wrong password should not verify
        assert auth_service.verify_password("wrong_password", hashed) == False

    def test_check_permissions(self, auth_service):
        """Test permission checking"""
        user_with_admin = {"roles": ["admin", "user"]}
        user_normal = {"roles": ["user"]}

        # Admin should have admin permissions
        assert auth_service.check_permissions(user_with_admin, "admin") == True

        # Normal user should not have admin permissions
        assert auth_service.check_permissions(user_normal, "admin") == False

        # Both should have user permissions
        assert auth_service.check_permissions(user_with_admin, "user") == True
        assert auth_service.check_permissions(user_normal, "user") == True


class TestEmbeddingService:
    """Unit tests for Embedding Service"""

    @pytest.fixture
    def embedding_service(self):
        """Embedding service with mocked OpenAI client"""
        service = EmbeddingService()
        service.openai_client = Mock()
        service.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        return service

    def test_embed_text_basic(self, embedding_service):
        """Test basic text embedding"""
        text = "This is a test document for embedding"

        embedding = embedding_service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # OpenAI ada-002 dimensions
        assert all(isinstance(x, (int, float)) for x in embedding)

    def test_embed_text_empty(self, embedding_service):
        """Test embedding empty text"""
        with pytest.raises(ValueError):
            embedding_service.embed_text("")

    def test_embed_text_very_long(self, embedding_service):
        """Test embedding very long text"""
        long_text = "word " * 10000  # Very long text

        # Should truncate or handle gracefully
        embedding = embedding_service.embed_text(long_text)
        assert isinstance(embedding, list)

    def test_batch_embed_texts(self, embedding_service):
        """Test batch embedding of multiple texts"""
        texts = [
            "First document for embedding",
            "Second document for embedding",
            "Third document for embedding",
        ]

        embeddings = embedding_service.batch_embed_texts(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

    def test_calculate_similarity(self, embedding_service):
        """Test similarity calculation between embeddings"""
        # Create two similar embeddings
        emb1 = [0.1] * 1536
        emb2 = [0.1] * 1536  # Identical
        emb3 = [0.9] * 1536  # Different

        # Identical embeddings should have high similarity
        similarity_high = embedding_service.calculate_similarity(emb1, emb2)
        assert similarity_high > 0.95

        # Different embeddings should have lower similarity
        similarity_low = embedding_service.calculate_similarity(emb1, emb3)
        assert similarity_low < similarity_high


# Utility tests for common functions
class TestUtilityFunctions:
    """Tests for utility functions used across the application"""

    def test_sanitize_input(self):
        """Test input sanitization"""
        from app.security.input_validation import sanitize_input

        # Test HTML injection
        dirty_input = "<script>alert('xss')</script>Hello"
        clean_input = sanitize_input(dirty_input)
        assert "<script>" not in clean_input
        assert "Hello" in clean_input

    def test_validate_email(self):
        """Test email validation"""
        from app.security.input_validation import validate_email

        # Valid emails
        assert validate_email("test@example.com") == True
        assert validate_email("user.name+tag@domain.co.uk") == True

        # Invalid emails
        assert validate_email("invalid.email") == False
        assert validate_email("@domain.com") == False
        assert validate_email("user@") == False

    def test_format_timestamp(self):
        """Test timestamp formatting"""
        from app.utils.datetime_utils import format_timestamp

        dt = datetime(2024, 1, 1, 12, 0, 0)
        formatted = format_timestamp(dt)

        assert isinstance(formatted, str)
        assert "2024" in formatted

    def test_calculate_text_similarity(self):
        """Test text similarity calculation"""
        from app.utils.text_utils import calculate_text_similarity

        text1 = "This is a test document"
        text2 = "This is a test document"  # Identical
        text3 = "Completely different content"

        # Identical texts should have high similarity
        similarity_high = calculate_text_similarity(text1, text2)
        assert similarity_high > 0.95

        # Different texts should have lower similarity
        similarity_low = calculate_text_similarity(text1, text3)
        assert similarity_low < similarity_high


# Performance and edge case tests
class TestPerformanceAndEdgeCases:
    """Tests for performance characteristics and edge cases"""

    def test_large_text_processing(self):
        """Test processing of large text documents"""
        from app.utils.text_processing import chunk_text

        # Create large text (1MB)
        large_text = "word " * 250000

        chunks = chunk_text(large_text, chunk_size=1000)

        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(len(chunk) <= 1000 for chunk in chunks)

    def test_concurrent_requests_simulation(self):
        """Test handling of concurrent requests (simulation)"""
        import asyncio

        async def mock_request():
            # Simulate async processing
            await asyncio.sleep(0.1)
            return {"status": "success"}

        async def test_concurrent():
            # Simulate 10 concurrent requests
            tasks = [mock_request() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 10
            assert all(r["status"] == "success" for r in results)

        # Run the test
        asyncio.run(test_concurrent())

    def test_memory_usage_tracking(self):
        """Test memory usage for large data structures"""
        import sys

        # Create large data structure
        large_list = [{"id": i, "data": "x" * 1000} for i in range(1000)]

        # Memory usage should be reasonable
        size = sys.getsizeof(large_list)
        assert size > 0

        # Cleanup
        del large_list


if __name__ == "__main__":
    # Запуск unit тестов
    pytest.main([__file__, "-v", "--tb=short"])
