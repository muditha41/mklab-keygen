"""Integration tests: auth + license CRUD (require DB with migrated schema)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_create_license_requires_auth(client: AsyncClient):
    r = await client.post(
        "/licenses/",
        json={
            "app_name": "TestApp",
            "client_name": "Test",
            "expiry_date": "2026-12-31",
            "status": "active",
            "monthly_renewal": True,
        },
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_patch_license_requires_auth(client: AsyncClient):
    r = await client.patch(
        "/licenses/00000000-0000-0000-0000-000000000001",
        json={"status": "inactive"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_delete_license_requires_auth(client: AsyncClient):
    r = await client.delete("/licenses/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_license_history_requires_auth(client: AsyncClient):
    r = await client.get("/licenses/00000000-0000-0000-0000-000000000001/history")
    assert r.status_code == 401
