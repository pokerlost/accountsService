"""SQLAlchemy model for human accounts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from persistence.database.base import UUIDModel
from persistence.database.mixins import TimestampMixin


class AccountModel(TimestampMixin, UUIDModel):
    """Persist one human account and its remote-principal binding."""

    __tablename__ = "accounts"
    __table_args__ = (
        PrimaryKeyConstraint(name="pk_accounts"),
        UniqueConstraint("username", name="uq_accounts_username"),
        UniqueConstraint("auth_principal_id", name="uq_accounts_auth_principal_id"),
        CheckConstraint(
            "username = lower(username)",
            name="ck_accounts_username_lowercase",
        ),
        CheckConstraint(
            "username ~ '^[a-z0-9_]{3,32}$'",
            name="ck_accounts_username_format",
        ),
        CheckConstraint(
            "nickname = btrim(nickname)",
            name="ck_accounts_nickname_canonical",
        ),
        CheckConstraint(
            "char_length(nickname) BETWEEN 1 AND 64",
            name="ck_accounts_nickname_length",
        ),
        CheckConstraint(
            "status IN ('pending', 'active', 'disabled')",
            name="ck_accounts_status",
        ),
        CheckConstraint(
            "role_snapshot IS NULL OR role_snapshot IN ('user', 'support', 'master')",
            name="ck_accounts_role_snapshot",
        ),
        CheckConstraint(
            "status = 'pending' OR auth_principal_id IS NOT NULL",
            name="ck_accounts_status_auth_principal",
        ),
    )

    auth_principal_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    role_snapshot: Mapped[str | None] = mapped_column(String(16), nullable=True)
