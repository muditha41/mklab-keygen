"""Auth routes (JWT) — Sprint 2."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.admin import Admin
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Admin login. Returns JWT access and refresh tokens."""
    result = await db.execute(select(Admin).where(Admin.email == body.email).limit(1))
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    admin.last_login = datetime.now(timezone.utc)
    await db.flush()
    return TokenResponse(
        access_token=create_access_token(admin.email),
        refresh_token=create_refresh_token(admin.email),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    """Exchange refresh token for new access and refresh tokens."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return TokenResponse(
        access_token=create_access_token(email),
        refresh_token=create_refresh_token(email),
    )
