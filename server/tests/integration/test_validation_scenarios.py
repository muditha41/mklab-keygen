"""Validation endpoint scenarios: invalid key, bad signature, expired timestamp, rate limit."""

import time
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import compute_validation_signature
from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_validate_invalid_signature_returns_200_valid_false(client: AsyncClient):
    """Invalid HMAC signature -> 200 with valid=false (no enumeration)."""
    ts = int(time.time())
    body = {
        "license_key": "LIC-FAKE-00000000-0000000000000000",
        "app_id": "test",
        "timestamp": ts,
        "signature": "wrong-signature",
    }
    r = await client.post("/licenses/validate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert "status" in data and "message" in data


@pytest.mark.asyncio
async def test_validate_stale_timestamp_returns_200_valid_false(client: AsyncClient):
    """Timestamp outside 5-min window -> valid=false."""
    body = {
        "license_key": "LIC-FAKE-00000000-0000000000000000",
        "app_id": "test",
        "timestamp": 0,
        "signature": "any",
    }
    r = await client.post("/licenses/validate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False


@pytest.mark.asyncio
async def test_validate_valid_signature_unknown_key_returns_200_valid_false(client: AsyncClient):
    """Valid signature but key not in DB -> valid=false."""
    ts = int(time.time())
    sig = compute_validation_signature("LIC-NOTINDB-00000000-ABCDEF0123456789", "app1", ts)
    body = {
        "license_key": "LIC-NOTINDB-00000000-ABCDEF0123456789",
        "app_id": "app1",
        "timestamp": ts,
        "signature": sig,
    }
    r = await client.post("/licenses/validate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert data.get("status") in ("invalid", "active", "expired", "pending")


@pytest.mark.asyncio
async def test_validate_missing_body_returns_422(client: AsyncClient):
    r = await client.post("/licenses/validate", json={})
    assert r.status_code == 422
