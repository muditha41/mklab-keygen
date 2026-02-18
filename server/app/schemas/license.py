"""License request/response schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Create ----
class LicenseCreate(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=255)
    client_name: str = Field(..., min_length=1, max_length=255)
    expiry_date: date
    status: str = Field(default="pending", pattern="^(active|inactive|suspended|pending)$")
    monthly_renewal: bool = True


# ---- Update (partial) ----
class LicenseUpdate(BaseModel):
    app_name: str | None = Field(None, min_length=1, max_length=255)
    client_name: str | None = Field(None, min_length=1, max_length=255)
    expiry_date: date | None = None
    status: str | None = Field(None, pattern="^(active|inactive|suspended|pending)$")
    monthly_renewal: bool | None = None


# ---- Response (no key) ----
class LicenseResponse(BaseModel):
    id: UUID
    app_name: str
    client_name: str
    expiry_date: date
    status: str
    monthly_renewal: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Create response (includes plaintext key ONCE) ----
class LicenseCreateResponse(BaseModel):
    id: UUID
    app_name: str
    client_name: str
    expiry_date: date
    status: str
    monthly_renewal: bool
    created_at: datetime
    license_key: str = Field(..., description="Show once; never stored or shown again")

    model_config = {"from_attributes": True}


# ---- Validation (public endpoint) ----
class ValidateRequest(BaseModel):
    license_key: str
    app_id: str = "default"
    timestamp: int  # Unix seconds
    signature: str


class ValidateResponse(BaseModel):
    valid: bool
    status: str  # active | expired | suspended | inactive | pending
    expires_at: datetime | None = None
    message: str


# ---- Validation history ----
class ValidationLogEntry(BaseModel):
    id: UUID
    license_id: UUID
    validated_at: datetime
    ip_address: str | None
    result: str
    error_reason: str | None

    model_config = {"from_attributes": True}
