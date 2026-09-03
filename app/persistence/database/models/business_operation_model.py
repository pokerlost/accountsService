"""SQLAlchemy model for resumable business operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from persistence.database.base import Base
from persistence.database.mixins import TimestampMixin


class BusinessOperationModel(TimestampMixin, Base):
    """Persist idempotency identity and recoverable distributed-mutation state."""

    __tablename__ = "business_operations"
    __table_args__ = (
        PrimaryKeyConstraint(name="pk_business_operations"),
        CheckConstraint(
            "operation_type IN ('register', 'create_staff', 'disable', 'enable', 'replace_scopes')",
            name="ck_business_operations_operation_type",
        ),
        CheckConstraint(
            "state IN "
            "('pending_remote', 'retryable_error', 'remote_applied', 'completed', 'blocked')",
            name="ck_business_operations_state",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_business_operations_attempt_count",
        ),
    )

    business_operation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    account_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "accounts.id",
            name="fk_business_operations_account_id_accounts",
        ),
        nullable=True,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    last_error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
