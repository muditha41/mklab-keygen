"""Validation log — audit trail for each validation request."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin


class ValidationLog(Base, UUIDMixin):
    """Single validation attempt: license_id, timestamp, IP, result, error_reason."""

    __tablename__ = "validation_logs"

    license_id: Mapped[UUID] = mapped_column(
        ForeignKey("licenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    result: Mapped[str] = mapped_column(String(16), nullable=False)  # success | fail
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    license: Mapped["License"] = relationship("License", back_populates="validation_logs")
