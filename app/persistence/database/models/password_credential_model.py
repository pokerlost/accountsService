"""SQLAlchemy model for account password credentials."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, PrimaryKeyConstraint, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from persistence.database.base import Base


class PasswordCredentialModel(Base):
    """Persist only an Argon2id PHC string and its change timestamps."""

    __tablename__ = "password_credentials"
    __table_args__ = (
        PrimaryKeyConstraint(name="pk_password_credentials"),
        CheckConstraint(
            "password_hash LIKE '$argon2id$%'",
            name="ck_password_credentials_password_hash_argon2id",
        ),
    )

    account_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "accounts.id",
            name="fk_password_credentials_account_id_accounts",
        ),
        primary_key=True,
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    hash_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
