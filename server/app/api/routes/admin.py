"""Admin dashboard routes (Jinja2 + HTMX) — Sprint 4 & 5."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ADMIN_TOKEN_COOKIE, get_admin_from_cookie, get_db
from app.core.security import create_access_token, verify_password
from app.models.admin import Admin
from app.schemas.license import LicenseCreate, LicenseUpdate
from app.services import license_service

router = APIRouter()
# Resolve templates path relative to this package (app/templates)
from pathlib import Path
_templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


def _set_token_cookie(response: RedirectResponse, token: str) -> None:
    response.set_cookie(
        key=ADMIN_TOKEN_COOKIE,
        value=token,
        httponly=True,
        max_age=900,  # 15 min
        samesite="lax",
    )


def _clear_token_cookie(response: RedirectResponse) -> None:
    response.delete_cookie(ADMIN_TOKEN_COOKIE)


# ---- Login ----
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login form."""
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Process login form; set cookie and redirect to dashboard."""
    from sqlalchemy import select

    result = await db.execute(select(Admin).where(Admin.email == email).limit(1))
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(password, admin.password_hash) or not admin.is_active:
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid email or password"},
            status_code=401,
        )
    token = create_access_token(admin.email)
    response = RedirectResponse(url="/admin", status_code=302)
    _set_token_cookie(response, token)
    return response


@router.post("/logout")
async def logout():
    """Clear cookie and redirect to login."""
    response = RedirectResponse(url="/admin/login", status_code=302)
    _clear_token_cookie(response)
    return response


# ---- Dashboard ----
@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    status: str | None = None,
    client_name: str | None = None,
    expiry_from: str | None = None,
    expiry_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin_from_cookie),
):
    """License list with optional filters and dashboard summary."""
    expiry_from_d = date.fromisoformat(expiry_from) if expiry_from else None
    expiry_to_d = date.fromisoformat(expiry_to) if expiry_to else None
    licenses = await license_service.list_licenses(
        db,
        status=status,
        client_name=client_name,
        expiry_from=expiry_from_d,
        expiry_to=expiry_to_d,
        limit=200,
    )
    active_count = await license_service.count_licenses_by_status(db, "active")
    expiring_soon = await license_service.list_licenses_expiring_soon(db, within_days=30)
    recent_failures = await license_service.list_recent_validation_failures(db, limit=10)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "licenses": licenses,
            "filter_status": status,
            "filter_client": client_name or "",
            "filter_expiry_from": expiry_from or "",
            "filter_expiry_to": expiry_to or "",
            "active_count": active_count,
            "expiring_soon": expiring_soon,
            "recent_failures": recent_failures,
        },
    )


@router.get("/licenses/new", response_class=HTMLResponse)
async def license_new_form(
    request: Request,
    admin: Admin = Depends(get_admin_from_cookie),
):
    """Create license form."""
    return templates.TemplateResponse(
        "admin/license_form.html",
        {"request": request, "admin": admin, "license": None, "created_key": None},
    )


@router.post("/licenses/new")
async def license_create(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin_from_cookie),
    app_name: str = Form(...),
    client_name: str = Form(...),
    expiry_date: str = Form(...),
    status: str = Form("pending"),
    monthly_renewal: str = Form("off"),  # "on" when checkbox checked
):
    """Create license; show form again with the new license key (show once)."""
    data = LicenseCreate(
        app_name=app_name.strip(),
        client_name=client_name.strip(),
        expiry_date=date.fromisoformat(expiry_date),
        status=status,
        monthly_renewal=monthly_renewal.lower() == "on",
    )
    license_, plain_key = await license_service.create_license(db, data)
    return templates.TemplateResponse(
        "admin/license_form.html",
        {
            "request": request,
            "admin": admin,
            "license": license_,
            "created_key": plain_key,
            "message": "License created. Copy the key below — it will not be shown again.",
        },
    )


@router.get("/licenses/{license_id}/edit", response_class=HTMLResponse)
async def license_edit_form(
    request: Request,
    license_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin_from_cookie),
):
    """Edit license form."""
    license_ = await license_service.get_license_by_id(db, license_id)
    if not license_:
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(
        "admin/license_edit.html",
        {"request": request, "admin": admin, "license": license_},
    )


@router.post("/licenses/{license_id}/edit")
async def license_update(
    request: Request,
    license_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin_from_cookie),
    app_name: str = Form(...),
    client_name: str = Form(...),
    expiry_date: str = Form(...),
    status: str = Form(...),
    monthly_renewal: str = Form("off"),
):
    """Update license and redirect to list."""
    license_ = await license_service.get_license_by_id(db, license_id)
    if not license_:
        return RedirectResponse(url="/admin", status_code=302)
    data = LicenseUpdate(
        app_name=app_name.strip(),
        client_name=client_name.strip(),
        expiry_date=date.fromisoformat(expiry_date),
        status=status,
        monthly_renewal=monthly_renewal.lower() == "on",
    )
    await license_service.update_license(db, license_, data)
    return RedirectResponse(url="/admin", status_code=302)


@router.post("/licenses/{license_id}/deactivate")
async def license_deactivate(
    license_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin_from_cookie),
):
    """Deactivate license and redirect to list."""
    license_ = await license_service.get_license_by_id(db, license_id)
    if license_:
        await license_service.deactivate_license(db, license_)
    return RedirectResponse(url="/admin", status_code=302)


# ---- Validation history (per license) ----
@router.get("/licenses/{license_id}/history", response_class=HTMLResponse)
async def license_history(
    request: Request,
    license_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin_from_cookie),
):
    """Validation history table for one license."""
    license_ = await license_service.get_license_by_id(db, license_id)
    if not license_:
        return RedirectResponse(url="/admin", status_code=302)
    logs = await license_service.list_validation_history(db, license_id, limit=200)
    return templates.TemplateResponse(
        "admin/license_history.html",
        {"request": request, "admin": admin, "license": license_, "logs": logs},
    )


# ---- Audit log (all validations) ----
@router.get("/audit", response_class=HTMLResponse)
async def audit_log(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin_from_cookie),
):
    """Full audit log: all validation attempts with IP, timestamp, result, error."""
    entries = await license_service.list_audit_logs(db, skip=skip, limit=limit)
    return templates.TemplateResponse(
        "admin/audit.html",
        {
            "request": request,
            "admin": admin,
            "entries": entries,
            "skip": skip,
            "limit": limit,
        },
    )
