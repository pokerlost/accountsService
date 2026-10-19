"""Remove business-operation fingerprint storage.

Revision ID: 20260901_0002
Revises: 20260829_0001
Create Date: 2026-09-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260901_0002"
down_revision: str | Sequence[str] | None = "20260829_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the retired keyed payload-digest fields."""
    op.drop_constraint(
        "ck_business_operations_payload_fingerprint_length",
        "business_operations",
        type_="check",
    )
    op.drop_constraint(
        "ck_business_operations_fingerprint_key_version",
        "business_operations",
        type_="check",
    )
    op.drop_column("business_operations", "fingerprint_key_version")
    op.drop_column("business_operations", "payload_fingerprint")


def downgrade() -> None:
    """Restore legacy fields with deterministic placeholders for existing rows."""
    op.add_column(
        "business_operations",
        sa.Column(
            "payload_fingerprint",
            postgresql.BYTEA(),
            server_default=sa.text("decode(repeat('00', 32), 'hex')"),
            nullable=False,
        ),
    )
    op.add_column(
        "business_operations",
        sa.Column(
            "fingerprint_key_version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.alter_column("business_operations", "payload_fingerprint", server_default=None)
    op.alter_column("business_operations", "fingerprint_key_version", server_default=None)
    op.create_check_constraint(
        "ck_business_operations_payload_fingerprint_length",
        "business_operations",
        "octet_length(payload_fingerprint) = 32",
    )
    op.create_check_constraint(
        "ck_business_operations_fingerprint_key_version",
        "business_operations",
        "fingerprint_key_version > 0",
    )
