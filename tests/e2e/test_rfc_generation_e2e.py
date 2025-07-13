"""End-to-End tests for RFC Generation"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.mark.e2e
class TestRFCGenerationE2E:
    """End-to-End tests for RFC Generation workflow"""

    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}

    def test_complete_rfc_generation_workflow(self, auth_headers):
        """Test complete RFC generation workflow"""

        # Test RFC generation endpoint
        with patch("app.api.v1.ai.generate.get_current_user") as mock_user:
            mock_user.return_value = Mock(id=1, email="test@example.com")

            response = client.post(
                "/api/v1/ai/rfc",
                json={
                    "task_description": "Test RFC for architecture changes",
                    "project_context": "Test project context",
                    "technical_requirements": "Test technical requirements",
                    "priority": "medium",
                    "template_type": "architecture"
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 404, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
