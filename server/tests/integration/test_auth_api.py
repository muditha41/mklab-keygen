"""Integration tests for auth and license APIs."""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_login_requires_body(client: AsyncClient):
    """Login with missing body returns 422."""
    r = await client.post("/auth/login", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Login with wrong credentials returns 401."""
    r = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_licenses_requires_auth(client: AsyncClient):
    """GET /licenses without Bearer token returns 401."""
    r = await client.get("/licenses/")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_validate_accepts_body(client: AsyncClient):
    """POST /licenses/validate with invalid body returns 422 or 200/400-style response."""
    r = await client.post(
        "/licenses/validate",
        json={
            "license_key": "LIC-TEST-00000000-0000000000000000",
            "app_id": "test",
            "timestamp": 0,
            "signature": "invalid",
        },
    )
    # Invalid timestamp (old) or invalid signature -> still 200 with valid: false
    assert r.status_code == 200
    data = r.json()
    assert "valid" in data
    assert data["valid"] is False
