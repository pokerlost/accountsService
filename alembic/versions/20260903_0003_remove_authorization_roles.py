"""Replace account workflow role state with exact scope sets.

Revision ID: 20260903_0003
Revises: 20260901_0002
Create Date: 2026-09-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260903_0003"
down_revision: str | Sequence[str] | None = "20260901_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_no_rows(*, description: str, query: str) -> None:
    """Reject a scope migration that would guess an authoritative permission set."""
    count = op.get_bind().execute(sa.text(query)).scalar_one()
    if not isinstance(count, int):
        raise RuntimeError("Role-removal precondition returned an invalid row count")
    if count != 0:
        raise RuntimeError(f"Cannot migrate {count} {description}; exact scopes are unavailable")


def _require_role_workflows_absent() -> None:
    """Require operators to resolve role-bearing workflows before schema conversion."""
    _require_no_rows(
        description="account provisioning workflow rows",
        query="SELECT count(*) FROM account_provisioning_operations",
    )
    _require_no_rows(
        description="role synchronization workflow rows",
        query=(
            "SELECT count(*) FROM account_synchronization_operations "
            "WHERE mutation_type = 'assign_role'"
        ),
    )
    _require_no_rows(
        description="role business operation rows",
        query="SELECT count(*) FROM business_operations WHERE operation_type = 'assign_role'",
    )


def upgrade() -> None:
    """Remove role state and introduce exact-scope workflow fields."""
    _require_role_workflows_absent()

    op.drop_constraint("ck_accounts_role_snapshot", "accounts", type_="check")
    op.drop_column("accounts", "role_snapshot")

    op.drop_constraint(
        "ck_account_provisioning_operations_requested_role",
        "account_provisioning_operations",
        type_="check",
    )
    op.drop_column("account_provisioning_operations", "requested_role")
    op.add_column(
        "account_provisioning_operations",
        sa.Column(
            "initial_scopes",
            postgresql.ARRAY(sa.String()),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_account_provisioning_operations_initial_scopes_no_nulls",
        "account_provisioning_operations",
        "array_position(initial_scopes, NULL) IS NULL",
    )

    op.drop_constraint(
        "ck_account_synchronization_operations_mutation_shape",
        "account_synchronization_operations",
        type_="check",
    )
    op.drop_constraint(
        "ck_account_synchronization_operations_desired_role",
        "account_synchronization_operations",
        type_="check",
    )
    op.drop_constraint(
        "ck_account_synchronization_operations_mutation_type",
        "account_synchronization_operations",
        type_="check",
    )
    op.drop_column("account_synchronization_operations", "desired_role")
    op.add_column(
        "account_synchronization_operations",
        sa.Column(
            "desired_scopes",
            postgresql.ARRAY(sa.String()),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_account_synchronization_operations_mutation_type",
        "account_synchronization_operations",
        "mutation_type IN ('set_status', 'replace_scopes')",
    )
    op.create_check_constraint(
        "ck_account_synchronization_operations_mutation_shape",
        "account_synchronization_operations",
        "(mutation_type = 'set_status' "
        "AND desired_status IS NOT NULL "
        "AND desired_scopes IS NULL) "
        "OR (mutation_type = 'replace_scopes' "
        "AND desired_status IS NULL "
        "AND desired_scopes IS NOT NULL "
        "AND array_position(desired_scopes, NULL) IS NULL)",
    )

    op.drop_constraint(
        "ck_business_operations_operation_type",
        "business_operations",
        type_="check",
    )
    op.create_check_constraint(
        "ck_business_operations_operation_type",
        "business_operations",
        "operation_type IN ('register', 'create_staff', 'disable', 'enable', 'replace_scopes')",
    )


def downgrade() -> None:
    """Restore the role schema only when no scope-bearing workflow would be lost."""
    _require_no_rows(
        description="account provisioning workflow rows",
        query="SELECT count(*) FROM account_provisioning_operations",
    )
    _require_no_rows(
        description="scope synchronization workflow rows",
        query=(
            "SELECT count(*) FROM account_synchronization_operations "
            "WHERE mutation_type = 'replace_scopes'"
        ),
    )
    _require_no_rows(
        description="scope business operation rows",
        query="SELECT count(*) FROM business_operations WHERE operation_type = 'replace_scopes'",
    )

    op.drop_constraint(
        "ck_business_operations_operation_type",
        "business_operations",
        type_="check",
    )
    op.create_check_constraint(
        "ck_business_operations_operation_type",
        "business_operations",
        "operation_type IN ('register', 'create_staff', 'disable', 'enable', 'assign_role')",
    )

    op.drop_constraint(
        "ck_account_synchronization_operations_mutation_shape",
        "account_synchronization_operations",
        type_="check",
    )
    op.drop_constraint(
        "ck_account_synchronization_operations_mutation_type",
        "account_synchronization_operations",
        type_="check",
    )
    op.drop_column("account_synchronization_operations", "desired_scopes")
    op.add_column(
        "account_synchronization_operations",
        sa.Column("desired_role", sa.String(length=16), nullable=True),
    )
    op.create_check_constraint(
        "ck_account_synchronization_operations_mutation_type",
        "account_synchronization_operations",
        "mutation_type IN ('set_status', 'assign_role')",
    )
    op.create_check_constraint(
        "ck_account_synchronization_operations_desired_role",
        "account_synchronization_operations",
        "desired_role IS NULL OR desired_role IN ('user', 'support', 'master')",
    )
    op.create_check_constraint(
        "ck_account_synchronization_operations_mutation_shape",
        "account_synchronization_operations",
        "(mutation_type = 'set_status' "
        "AND desired_status IS NOT NULL "
        "AND desired_role IS NULL) "
        "OR (mutation_type = 'assign_role' "
        "AND desired_status IS NULL "
        "AND desired_role IS NOT NULL)",
    )

    op.drop_constraint(
        "ck_account_provisioning_operations_initial_scopes_no_nulls",
        "account_provisioning_operations",
        type_="check",
    )
    op.drop_column("account_provisioning_operations", "initial_scopes")
    op.add_column(
        "account_provisioning_operations",
        sa.Column("requested_role", sa.String(length=16), nullable=False),
    )
    op.create_check_constraint(
        "ck_account_provisioning_operations_requested_role",
        "account_provisioning_operations",
        "requested_role IN ('user', 'support', 'master')",
    )

    op.add_column(
        "accounts",
        sa.Column("role_snapshot", sa.String(length=16), nullable=True),
    )
    op.create_check_constraint(
        "ck_accounts_role_snapshot",
        "accounts",
        "role_snapshot IS NULL OR role_snapshot IN ('user', 'support', 'master')",
    )
