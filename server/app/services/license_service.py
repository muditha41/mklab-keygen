"""License business logic: key generation, CRUD, validation."""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    generate_license_key,
    hash_license_key,
    verify_validation_signature,
)
from app.models.license import License
from app.models.validation_log import ValidationLog
from app.schemas.license import LicenseCreate, LicenseUpdate, ValidateRequest, ValidateResponse


def create_license_key_pair(app_code: str) -> tuple[str, str]:
    """
    Generate a new license key and its hash for DB storage.
    Returns (plaintext_key, key_hash). Caller must show plaintext once and store only hash.
    """
    plain = generate_license_key(app_code)
    key_hash = hash_license_key(plain)
    return plain, key_hash


# ---- CRUD ----
async def create_license(db: AsyncSession, data: LicenseCreate) -> tuple[License, str]:
    """Create license; returns (license, plaintext_key). Extract app_code from app_name (e.g. MYAPP)."""
    app_code = (data.app_name or "APP").replace(" ", "")[:20].upper() or "APP"
    plain_key, key_hash = create_license_key_pair(app_code)
    license_ = License(
        license_key_hash=key_hash,
        app_name=data.app_name,
        client_name=data.client_name,
        expiry_date=data.expiry_date,
        status=data.status,
        monthly_renewal=data.monthly_renewal,
    )
    db.add(license_)
    await db.flush()
    await db.refresh(license_)
    return license_, plain_key


async def list_licenses(
    db: AsyncSession,
    *,
    status: str | None = None,
    client_name: str | None = None,
    expiry_from: date | None = None,
    expiry_to: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[License]:
    """List licenses with optional filters (status, client, expiry date range)."""
    q = select(License).order_by(License.created_at.desc()).offset(skip).limit(limit)
    if status:
        q = q.where(License.status == status)
    if client_name:
        q = q.where(License.client_name.ilike(f"%{client_name}%"))
    if expiry_from is not None:
        q = q.where(License.expiry_date >= expiry_from)
    if expiry_to is not None:
        q = q.where(License.expiry_date <= expiry_to)
    result = await db.execute(q)
    return list(result.scalars().all())


async def count_licenses_by_status(db: AsyncSession, status: str) -> int:
    """Count licenses with the given status."""
    from sqlalchemy import func
    r = await db.execute(select(func.count()).select_from(License).where(License.status == status))
    return r.scalar() or 0


async def list_licenses_expiring_soon(
    db: AsyncSession, within_days: int = 30
) -> list[License]:
    """Licenses whose expiry_date is in [today, today + within_days]."""
    today = date.today()
    end = today + timedelta(days=within_days)
    q = (
        select(License)
        .where(License.expiry_date >= today, License.expiry_date <= end)
        .order_by(License.expiry_date.asc())
        .limit(50)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_recent_validation_failures(
    db: AsyncSession, limit: int = 20
) -> list[tuple[ValidationLog, License]]:
    """Recent validation attempts that failed (result='fail'), with license."""
    q = (
        select(ValidationLog, License)
        .join(License, ValidationLog.license_id == License.id)
        .where(ValidationLog.result == "fail")
        .order_by(ValidationLog.validated_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    return [(row[0], row[1]) for row in result.all()]


async def list_validation_history(
    db: AsyncSession, license_id: UUID, limit: int = 500
) -> list[ValidationLog]:
    """Validation log entries for one license, newest first."""
    q = (
        select(ValidationLog)
        .where(ValidationLog.license_id == license_id)
        .order_by(ValidationLog.validated_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_audit_logs(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[tuple[ValidationLog, License]]:
    """All validation logs with license info (app_name, client_name), for audit view."""
    q = (
        select(ValidationLog, License)
        .join(License, ValidationLog.license_id == License.id)
        .order_by(ValidationLog.validated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(q)
    return [(row[0], row[1]) for row in result.all()]


async def get_license_by_id(db: AsyncSession, license_id: UUID) -> License | None:
    """Get a single license by id."""
    result = await db.execute(select(License).where(License.id == license_id).limit(1))
    return result.scalar_one_or_none()


async def update_license(
    db: AsyncSession, license_: License, data: LicenseUpdate
) -> License:
    """Update license fields."""
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(license_, k, v)
    await db.flush()
    await db.refresh(license_)
    return license_


async def deactivate_license(db: AsyncSession, license_: License) -> License:
    """Set license status to inactive (soft delete)."""
    license_.status = "inactive"
    await db.flush()
    await db.refresh(license_)
    return license_


# ---- Validation ----
def _check_timestamp_fresh(timestamp: int) -> bool:
    """Request timestamp must be within 5-minute window."""
    now = int(datetime.now(timezone.utc).timestamp())
    delta = abs(now - timestamp)
    return delta <= settings.validation_timestamp_window_seconds


async def validate_license(
    db: AsyncSession,
    body: ValidateRequest,
    ip_address: str | None = None,
) -> ValidateResponse:
    """
    Validate a license key: verify signature and timestamp, lookup by hash,
    check status and expiry, log result. Returns minimal response to avoid enumeration.
    """
    # 1. Verify signature and timestamp
    if not _check_timestamp_fresh(body.timestamp):
        return ValidateResponse(
            valid=False,
            status="invalid",
            expires_at=None,
            message="Request expired or invalid timestamp",
        )
    if not verify_validation_signature(
        body.license_key, body.app_id, body.timestamp, body.signature
    ):
        await _log_validation(db, None, ip_address, "fail", "Invalid signature")
        return ValidateResponse(
            valid=False,
            status="invalid",
            expires_at=None,
            message="Invalid request",
        )

    key_hash = hash_license_key(body.license_key)
    result = await db.execute(
        select(License).where(License.license_key_hash == key_hash).limit(1)
    )
    license_ = result.scalar_one_or_none()

    if not license_:
        await _log_validation(db, None, ip_address, "fail", "License not found")
        return ValidateResponse(
            valid=False,
            status="invalid",
            expires_at=None,
            message="Invalid license",
        )

    # 2. Check status and expiry
    expiry_dt = datetime.combine(license_.expiry_date, datetime.min.time())
    expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if now > expiry_dt:
        await _log_validation(db, license_.id, ip_address, "fail", "License expired")
        return ValidateResponse(
            valid=False,
            status="expired",
            expires_at=expiry_dt,
            message="License has expired",
        )
    if license_.status == "inactive":
        await _log_validation(db, license_.id, ip_address, "fail", "License inactive")
        return ValidateResponse(
            valid=False,
            status="inactive",
            expires_at=expiry_dt,
            message="License is inactive",
        )
    if license_.status == "suspended":
        await _log_validation(db, license_.id, ip_address, "fail", "License suspended")
        return ValidateResponse(
            valid=False,
            status="suspended",
            expires_at=expiry_dt,
            message="License is suspended",
        )
    if license_.status == "pending":
        await _log_validation(db, license_.id, ip_address, "success", None)
        return ValidateResponse(
            valid=False,
            status="pending",
            expires_at=expiry_dt,
            message="License is pending activation",
        )

    # status == "active"
    await _log_validation(db, license_.id, ip_address, "success", None)
    return ValidateResponse(
        valid=True,
        status="active",
        expires_at=expiry_dt,
        message="License valid",
    )


async def _log_validation(
    db: AsyncSession,
    license_id: UUID | None,
    ip_address: str | None,
    result: str,
    error_reason: str | None,
) -> None:
    """Insert a validation_log row."""
    if license_id is None:
        return  # We don't have a license id for "not found" cases; could use a sentinel
    log = ValidationLog(
        license_id=license_id,
        ip_address=ip_address,
        result=result,
        error_reason=error_reason,
    )
    db.add(log)
    await db.flush()
