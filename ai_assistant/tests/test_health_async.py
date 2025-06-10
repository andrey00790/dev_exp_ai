import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.append(str(Path(__file__).resolve().parents[2]))

from ai_assistant.app.main import app

@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
