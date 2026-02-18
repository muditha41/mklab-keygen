"""Health endpoint and basic API tests."""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def client():
    """Async HTTP client for the FastAPI app."""
    from httpx import ASGITransport
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    """GET /health returns 200 and status ok."""
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "swaps"
