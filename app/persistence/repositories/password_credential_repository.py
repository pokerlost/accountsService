"""Narrow SQLAlchemy persistence adapter for password credentials."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import insert, select, update

from domain.accounts import PasswordCredential
from persistence.database.models import PasswordCredentialModel

from .base import SQLAlchemyRepository


def _to_domain(model: PasswordCredentialModel) -> PasswordCredential:
    """Hydrate a credential without exposing its PHC value in diagnostics."""
    return PasswordCredential.hydrate(
        account_id=model.account_id,
        password_hash=model.password_hash,
        password_changed_at=model.password_changed_at,
        hash_updated_at=model.hash_updated_at,
    )


class PasswordCredentialRepository(SQLAlchemyRepository):
    """Persist the single password credential owned by a human account."""

    async def add(self, credential: PasswordCredential) -> PasswordCredential:
        """Insert and return one validated Argon2id credential."""
        result = await self._read_scalar(
            insert(PasswordCredentialModel)
            .values(
                account_id=credential.account_id,
                password_hash=credential.password_hash,
                password_changed_at=credential.password_changed_at,
                hash_updated_at=credential.hash_updated_at,
            )
            .returning(PasswordCredentialModel),
        )
        return _to_domain(result.one())

    async def get_by_account_id(self, account_id: UUID) -> PasswordCredential | None:
        """Return the credential belonging to one human account."""
        result = await self._read_scalar(
            select(PasswordCredentialModel).where(
                PasswordCredentialModel.account_id == account_id,
            ),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def replace_hash_if_current(
        self,
        credential: PasswordCredential,
        *,
        expected_password_hash: str,
    ) -> PasswordCredential | None:
        """Replace a PHC value only if no concurrent password change won the race."""
        result = await self._read_scalar(
            update(PasswordCredentialModel)
            .where(
                PasswordCredentialModel.account_id == credential.account_id,
                PasswordCredentialModel.password_hash == expected_password_hash,
            )
            .values(
                password_hash=credential.password_hash,
                hash_updated_at=credential.hash_updated_at,
            )
            .returning(PasswordCredentialModel),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None
