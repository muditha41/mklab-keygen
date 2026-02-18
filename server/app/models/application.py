"""Application model — which app a license covers."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Application(Base, UUIDMixin, TimestampMixin):
    """Registered application that can have licenses."""

    __tablename__ = "applications"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    owner_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # licenses: Mapped[list["License"]] = relationship("License", back_populates="application")
