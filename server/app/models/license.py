"""License model — key hash, status, expiry."""

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class License(Base, UUIDMixin, TimestampMixin):
    """
    License record. license_key is stored as SHA256 hash only; plaintext shown once at creation.
    """

    __tablename__ = "licenses"

    license_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    app_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    monthly_renewal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    application_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
    )

    validation_logs: Mapped[list["ValidationLog"]] = relationship(
        "ValidationLog",
        back_populates="license",
        order_by="ValidationLog.validated_at.desc()",
    )
