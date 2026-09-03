"""SQLAlchemy model for account-provisioning workflow state."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from persistence.database.base import Base
from persistence.database.mixins import TimestampMixin


class AccountProvisioningOperationModel(TimestampMixin, Base):
    """Persist local progress for provisioning a human principal."""

    __tablename__ = "account_provisioning_operations"
    __table_args__ = (
        PrimaryKeyConstraint(name="pk_account_provisioning_operations"),
        UniqueConstraint(
            "account_id",
            name="uq_account_provisioning_operations_account_id",
        ),
        CheckConstraint(
            "array_position(initial_scopes, NULL) IS NULL",
            name="ck_account_provisioning_operations_initial_scopes_no_nulls",
        ),
        CheckConstraint(
            "remote_principal_status IS NULL OR remote_principal_status IN ('active', 'disabled')",
            name="ck_account_provisioning_operations_remote_principal_status",
        ),
    )

    business_operation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "business_operations.business_operation_id",
            name="fk_account_provisioning_operations_business_operation",
        ),
        primary_key=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "accounts.id",
            name="fk_account_provisioning_operations_account_id_accounts",
        ),
        nullable=False,
    )
    initial_scopes: Mapped[list[str]] = mapped_column(ARRAY(String()), nullable=False)
    remote_principal_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    remote_principal_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
