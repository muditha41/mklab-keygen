"""Pytest fixtures: test client for API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    """Async HTTP client for the FastAPI app (no DB override)."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
