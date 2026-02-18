"""Unit tests for license service (pure functions and logic with mocked DB)."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.schemas.license import LicenseCreate, ValidateRequest, ValidateResponse
from app.services import license_service


def test_create_license_key_pair():
    plain, key_hash = license_service.create_license_key_pair("APP")
    assert plain.startswith("LIC-APP-")
    assert len(key_hash) == 64
    assert all(c in "0123456789abcdef" for c in key_hash)


@pytest.mark.asyncio
async def test_create_license_returns_plain_key():
    db = AsyncMock()
    data = LicenseCreate(
        app_name="MyApp",
        client_name="Acme",
        expiry_date=date(2026, 12, 31),
        status="active",
        monthly_renewal=True,
    )
    license_, plain = await license_service.create_license(db, data)
    assert license_.app_name == "MyApp"
    assert license_.client_name == "Acme"
    assert plain.startswith("LIC-")
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_validate_license_stale_timestamp_returns_invalid():
    """Request with timestamp outside 5-min window returns valid=False."""
    body = ValidateRequest(
        license_key="LIC-X-00000000-0000000000000000",
        app_id="default",
        timestamp=0,
        signature="any",
    )
    db = AsyncMock()
    resp = await license_service.validate_license(db, body)
    assert isinstance(resp, ValidateResponse)
    assert resp.valid is False
    assert resp.status == "invalid"
