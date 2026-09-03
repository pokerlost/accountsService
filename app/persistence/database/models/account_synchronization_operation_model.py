"""SQLAlchemy model for account-synchronization workflow state."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import ARRAY, CheckConstraint, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from persistence.database.base import Base
from persistence.database.mixins import TimestampMixin


class AccountSynchronizationOperationModel(TimestampMixin, Base):
    """Persist one requested status or exact-scope mutation for reconciliation."""

    __tablename__ = "account_synchronization_operations"
    __table_args__ = (
        PrimaryKeyConstraint(name="pk_account_synchronization_operations"),
        CheckConstraint(
            "mutation_type IN ('set_status', 'replace_scopes')",
            name="ck_account_synchronization_operations_mutation_type",
        ),
        CheckConstraint(
            "desired_status IS NULL OR desired_status IN ('active', 'disabled')",
            name="ck_account_synchronization_operations_desired_status",
        ),
        CheckConstraint(
            "(mutation_type = 'set_status' "
            "AND desired_status IS NOT NULL "
            "AND desired_scopes IS NULL) "
            "OR (mutation_type = 'replace_scopes' "
            "AND desired_status IS NULL "
            "AND desired_scopes IS NOT NULL "
            "AND array_position(desired_scopes, NULL) IS NULL)",
            name="ck_account_synchronization_operations_mutation_shape",
        ),
    )

    business_operation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "business_operations.business_operation_id",
            name="fk_account_synchronization_operations_business_operation",
        ),
        primary_key=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "accounts.id",
            name="fk_account_synchronization_operations_account_id_accounts",
        ),
        nullable=False,
    )
    mutation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    desired_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    desired_scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String()), nullable=True)
