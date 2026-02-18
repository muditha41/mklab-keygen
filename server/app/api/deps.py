"""FastAPI dependencies: DB session, current admin (JWT), dashboard cookie auth."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.admin import Admin

security = HTTPBearer(auto_error=False)

# Cookie name for dashboard (browser) auth
ADMIN_TOKEN_COOKIE = "swaps_token"
ADMIN_LOGIN_PATH = "/admin/login"


async def get_current_admin(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Admin:
    """Require valid JWT and return the admin. Use for protected routes."""
    if not credentials or credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(Admin).where(Admin.email == email).limit(1))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin inactive")
    return admin


async def get_optional_admin(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Admin | None:
    """Optional admin from JWT. Returns None if no/invalid token."""
    if not credentials or credentials.scheme != "Bearer":
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    email = payload.get("sub")
    if not email:
        return None
    result = await db.execute(select(Admin).where(Admin.email == email).limit(1))
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        return None
    return admin


async def get_admin_from_cookie(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """
    For dashboard HTML routes: require admin from swaps_token cookie.
    Redirects to /admin/login if missing or invalid.
    """
    token = request.cookies.get(ADMIN_TOKEN_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": ADMIN_LOGIN_PATH},
        )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": ADMIN_LOGIN_PATH},
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": ADMIN_LOGIN_PATH},
        )
    result = await db.execute(select(Admin).where(Admin.email == email).limit(1))
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": ADMIN_LOGIN_PATH},
        )
    return admin
