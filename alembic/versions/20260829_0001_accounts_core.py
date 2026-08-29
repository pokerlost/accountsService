"""Create account core persistence.

Revision ID: 20260829_0001
Revises: None
Create Date: 2026-08-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260829_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create account and resumable-workflow tables."""
    op.create_table(
        "accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("auth_principal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("nickname", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("role_snapshot", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "username = lower(username)",
            name="ck_accounts_username_lowercase",
        ),
        sa.CheckConstraint(
            "username ~ '^[a-z0-9_]{3,32}$'",
            name="ck_accounts_username_format",
        ),
        sa.CheckConstraint(
            "nickname = btrim(nickname)",
            name="ck_accounts_nickname_canonical",
        ),
        sa.CheckConstraint(
            "char_length(nickname) BETWEEN 1 AND 64",
            name="ck_accounts_nickname_length",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'disabled')",
            name="ck_accounts_status",
        ),
        sa.CheckConstraint(
            "role_snapshot IS NULL OR role_snapshot IN ('user', 'support', 'master')",
            name="ck_accounts_role_snapshot",
        ),
        sa.CheckConstraint(
            "status = 'pending' OR auth_principal_id IS NOT NULL",
            name="ck_accounts_status_auth_principal",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_accounts"),
        sa.UniqueConstraint("auth_principal_id", name="uq_accounts_auth_principal_id"),
        sa.UniqueConstraint("username", name="uq_accounts_username"),
    )

    op.create_table(
        "password_credentials",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hash_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "password_hash LIKE '$argon2id$%'",
            name="ck_password_credentials_password_hash_argon2id",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_password_credentials_account_id_accounts",
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_password_credentials"),
    )

    op.create_table(
        "business_operations",
        sa.Column("business_operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column("payload_fingerprint", postgresql.BYTEA(), nullable=False),
        sa.Column("fingerprint_key_version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_error_code", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "operation_type IN ('register', 'create_staff', 'disable', 'enable', 'assign_role')",
            name="ck_business_operations_operation_type",
        ),
        sa.CheckConstraint(
            "octet_length(payload_fingerprint) = 32",
            name="ck_business_operations_payload_fingerprint_length",
        ),
        sa.CheckConstraint(
            "fingerprint_key_version > 0",
            name="ck_business_operations_fingerprint_key_version",
        ),
        sa.CheckConstraint(
            "state IN "
            "('pending_remote', 'retryable_error', 'remote_applied', 'completed', 'blocked')",
            name="ck_business_operations_state",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_business_operations_attempt_count",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_business_operations_account_id_accounts",
        ),
        sa.PrimaryKeyConstraint("business_operation_id", name="pk_business_operations"),
    )

    op.create_table(
        "account_provisioning_operations",
        sa.Column("business_operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_role", sa.String(length=16), nullable=False),
        sa.Column("remote_principal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("remote_principal_status", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "requested_role IN ('user', 'support', 'master')",
            name="ck_account_provisioning_operations_requested_role",
        ),
        sa.CheckConstraint(
            "remote_principal_status IS NULL OR remote_principal_status IN ('active', 'disabled')",
            name="ck_account_provisioning_operations_remote_principal_status",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_provisioning_operations_account_id_accounts",
        ),
        sa.ForeignKeyConstraint(
            ["business_operation_id"],
            ["business_operations.business_operation_id"],
            name="fk_account_provisioning_operations_business_operation",
        ),
        sa.PrimaryKeyConstraint(
            "business_operation_id",
            name="pk_account_provisioning_operations",
        ),
        sa.UniqueConstraint(
            "account_id",
            name="uq_account_provisioning_operations_account_id",
        ),
    )

    op.create_table(
        "account_synchronization_operations",
        sa.Column("business_operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mutation_type", sa.String(length=16), nullable=False),
        sa.Column("desired_status", sa.String(length=16), nullable=True),
        sa.Column("desired_role", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "mutation_type IN ('set_status', 'assign_role')",
            name="ck_account_synchronization_operations_mutation_type",
        ),
        sa.CheckConstraint(
            "desired_status IS NULL OR desired_status IN ('active', 'disabled')",
            name="ck_account_synchronization_operations_desired_status",
        ),
        sa.CheckConstraint(
            "desired_role IS NULL OR desired_role IN ('user', 'support', 'master')",
            name="ck_account_synchronization_operations_desired_role",
        ),
        sa.CheckConstraint(
            "(mutation_type = 'set_status' "
            "AND desired_status IS NOT NULL "
            "AND desired_role IS NULL) "
            "OR (mutation_type = 'assign_role' "
            "AND desired_status IS NULL "
            "AND desired_role IS NOT NULL)",
            name="ck_account_synchronization_operations_mutation_shape",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_synchronization_operations_account_id_accounts",
        ),
        sa.ForeignKeyConstraint(
            ["business_operation_id"],
            ["business_operations.business_operation_id"],
            name="fk_account_synchronization_operations_business_operation",
        ),
        sa.PrimaryKeyConstraint(
            "business_operation_id",
            name="pk_account_synchronization_operations",
        ),
    )


def downgrade() -> None:
    """Drop account and resumable-workflow tables in dependency-safe order."""
    op.drop_table("account_synchronization_operations")
    op.drop_table("account_provisioning_operations")
    op.drop_table("business_operations")
    op.drop_table("password_credentials")
    op.drop_table("accounts")
