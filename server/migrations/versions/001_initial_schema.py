"""Initial schema: applications, admins, licenses, validation_logs.

Revision ID: 001_initial
Revises:
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("owner_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_name"), "applications", ["name"], unique=False)

    op.create_table(
        "admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admins_email"), "admins", ["email"], unique=True)

    op.create_table(
        "licenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_key_hash", sa.String(64), nullable=False),
        sa.Column("app_name", sa.String(255), nullable=False),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("monthly_renewal", sa.Boolean(), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_licenses_app_name"), "licenses", ["app_name"], unique=False)
    op.create_index(op.f("ix_licenses_client_name"), "licenses", ["client_name"], unique=False)
    op.create_index(op.f("ix_licenses_license_key_hash"), "licenses", ["license_key_hash"], unique=True)
    op.create_index(op.f("ix_licenses_status"), "licenses", ["status"], unique=False)

    op.create_table(
        "validation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("validated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column("error_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_validation_logs_license_id"), "validation_logs", ["license_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_validation_logs_license_id"), table_name="validation_logs")
    op.drop_table("validation_logs")
    op.drop_index(op.f("ix_licenses_status"), table_name="licenses")
    op.drop_index(op.f("ix_licenses_license_key_hash"), table_name="licenses")
    op.drop_index(op.f("ix_licenses_client_name"), table_name="licenses")
    op.drop_index(op.f("ix_licenses_app_name"), table_name="licenses")
    op.drop_table("licenses")
    op.drop_index(op.f("ix_admins_email"), table_name="admins")
    op.drop_table("admins")
    op.drop_index(op.f("ix_applications_name"), table_name="applications")
    op.drop_table("applications")
