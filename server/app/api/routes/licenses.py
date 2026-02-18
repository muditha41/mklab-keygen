"""License CRUD and validation routes."""

from collections import deque
from datetime import date
from time import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_admin, get_db
from app.core.security import hash_license_key
from app.models.license import License
from app.models.validation_log import ValidationLog
from app.schemas.license import (
    LicenseCreate,
    LicenseCreateResponse,
    LicenseResponse,
    LicenseUpdate,
    ValidateRequest,
    ValidateResponse,
    ValidationLogEntry,
)
from app.services import license_service

router = APIRouter()

# In-memory rate limit: key_hash -> deque of timestamps (last hour). Sprint 6: use Redis.
_validations_by_key: dict[str, deque[float]] = {}
_RATE_LIMIT_PER_HOUR = 10
_HOUR_SECONDS = 3600


def _check_validation_rate_limit(license_key: str) -> bool:
    """True if under limit (allow), False if over limit (reject)."""
    key_hash = hash_license_key(license_key)
    now = time()
    if key_hash not in _validations_by_key:
        _validations_by_key[key_hash] = deque(maxlen=_RATE_LIMIT_PER_HOUR + 1)
    q = _validations_by_key[key_hash]
    while q and q[0] < now - _HOUR_SECONDS:
        q.popleft()
    if len(q) >= _RATE_LIMIT_PER_HOUR:
        return False
    q.append(now)
    return True


@router.post("/", response_model=LicenseCreateResponse)
async def create_license(
    body: LicenseCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
) -> LicenseCreateResponse:
    """Create a new license. Plaintext key returned only in this response."""
    license_, plain_key = await license_service.create_license(db, body)
    return LicenseCreateResponse(
        id=license_.id,
        app_name=license_.app_name,
        client_name=license_.client_name,
        expiry_date=license_.expiry_date,
        status=license_.status,
        monthly_renewal=license_.monthly_renewal,
        created_at=license_.created_at,
        license_key=plain_key,
    )


@router.get("/", response_model=list[LicenseResponse])
async def list_licenses(
    status: str | None = None,
    client_name: str | None = None,
    expiry_from: date | None = None,
    expiry_to: date | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
) -> list[LicenseResponse]:
    """List all licenses with optional filters (admin only)."""
    items = await license_service.list_licenses(
        db,
        status=status,
        client_name=client_name,
        expiry_from=expiry_from,
        expiry_to=expiry_to,
        skip=skip,
        limit=limit,
    )
    return [LicenseResponse.model_validate(x) for x in items]


@router.post("/validate", response_model=ValidateResponse)
async def validate_license(
    body: ValidateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ValidateResponse:
    """Public endpoint: validate a license key (called by SDK). Signed request required."""
    if not _check_validation_rate_limit(body.license_key):
        return ValidateResponse(
            valid=False,
            status="rate_limited",
            expires_at=None,
            message="Too many validation attempts; try again later",
        )
    ip_address = request.client.host if request.client else None
    return await license_service.validate_license(db, body, ip_address=ip_address)


# Path for validate must not match /{id}; so we define validate above and {id} below.
@router.get("/{license_id}", response_model=LicenseResponse)
async def get_license(
    license_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
) -> LicenseResponse:
    """Get single license details (admin only)."""
    license_ = await license_service.get_license_by_id(db, license_id)
    if not license_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    return LicenseResponse.model_validate(license_)


@router.patch("/{license_id}", response_model=LicenseResponse)
async def update_license(
    license_id: UUID,
    body: LicenseUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
) -> LicenseResponse:
    """Update license fields (admin only)."""
    license_ = await license_service.get_license_by_id(db, license_id)
    if not license_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    updated = await license_service.update_license(db, license_, body)
    return LicenseResponse.model_validate(updated)


@router.delete("/{license_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_license(
    license_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
) -> None:
    """Soft-delete / deactivate a license (admin only)."""
    license_ = await license_service.get_license_by_id(db, license_id)
    if not license_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    await license_service.deactivate_license(db, license_)


@router.get("/{license_id}/history", response_model=list[ValidationLogEntry])
async def get_license_history(
    license_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
) -> list[ValidationLogEntry]:
    """Get validation history for a license (admin only)."""
    result = await db.execute(
        select(ValidationLog)
        .where(ValidationLog.license_id == license_id)
        .order_by(ValidationLog.validated_at.desc())
        .limit(500)
    )
    logs = list(result.scalars().all())
    return [ValidationLogEntry.model_validate(x) for x in logs]
