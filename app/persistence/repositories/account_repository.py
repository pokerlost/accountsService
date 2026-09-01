"""Narrow SQLAlchemy persistence adapter for human accounts."""

from __future__ import annotations

from uuid import UUID

from pypokerlost.types import AuthorizationRole
from sqlalchemy import insert, select, update

from domain.accounts import Account, CanonicalUsername, Nickname
from domain.enums import AccountStatus
from persistence.database.models import AccountModel

from .base import SQLAlchemyRepository

_ALLOWED_PREVIOUS_STATUSES: dict[AccountStatus, tuple[AccountStatus, ...]] = {
    AccountStatus.ACTIVE: (AccountStatus.PENDING, AccountStatus.DISABLED),
    AccountStatus.DISABLED: (AccountStatus.ACTIVE,),
}


def _to_domain(model: AccountModel) -> Account:
    """Hydrate a framework-independent account from one ORM row."""
    return Account.hydrate(
        id=model.id,
        auth_principal_id=model.auth_principal_id,
        username=CanonicalUsername(model.username),
        nickname=Nickname(model.nickname),
        status=AccountStatus(model.status),
        role_snapshot=(
            AuthorizationRole(model.role_snapshot) if model.role_snapshot is not None else None
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class AccountRepository(SQLAlchemyRepository):
    """Persist human accounts through account-specific statements."""

    async def add(self, account: Account) -> Account:
        """Insert and return one validated human account."""
        result = await self._read_scalar(
            insert(AccountModel)
            .values(
                id=account.id,
                auth_principal_id=account.auth_principal_id,
                username=account.username.value,
                nickname=account.nickname.value,
                status=account.status.value,
                role_snapshot=(
                    account.role_snapshot.value if account.role_snapshot is not None else None
                ),
                created_at=account.created_at,
                updated_at=account.updated_at,
            )
            .returning(AccountModel),
        )
        return _to_domain(result.one())

    async def get_by_id(self, account_id: UUID) -> Account | None:
        """Return an account by its stable local identifier."""
        result = await self._read_scalar(
            select(AccountModel).where(AccountModel.id == account_id),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def get_by_id_for_update(self, account_id: UUID) -> Account | None:
        """Lock and return an account for a coordinated domain mutation."""
        result = await self._read_scalar(
            select(AccountModel).where(AccountModel.id == account_id).with_for_update(),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def get_by_canonical_username(
        self,
        username: CanonicalUsername,
    ) -> Account | None:
        """Return an account through the sole canonical login identifier path."""
        result = await self._read_scalar(
            select(AccountModel).where(AccountModel.username == username.value),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def bind_auth_principal(self, account: Account) -> Account | None:
        """Bind an auth principal once using compare-and-set semantics."""
        if account.auth_principal_id is None:
            raise ValueError("Principal binding requires a bound domain account.")

        result = await self._read_scalar(
            update(AccountModel)
            .where(
                AccountModel.id == account.id,
                AccountModel.auth_principal_id.is_(None),
            )
            .values(
                auth_principal_id=account.auth_principal_id,
                updated_at=account.updated_at,
            )
            .returning(AccountModel),
        )
        model = result.one_or_none()
        if model is not None:
            return _to_domain(model)

        existing_result = await self._read_scalar(
            select(AccountModel).where(AccountModel.id == account.id).with_for_update(),
        )
        existing = existing_result.one_or_none()
        if existing is None or existing.auth_principal_id != account.auth_principal_id:
            return None
        return _to_domain(existing)

    async def update_nickname(self, account: Account) -> Account | None:
        """Persist the current validated nickname of an account."""
        result = await self._read_scalar(
            update(AccountModel)
            .where(AccountModel.id == account.id)
            .values(
                nickname=account.nickname.value,
                updated_at=account.updated_at,
            )
            .returning(AccountModel),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def transition_status(self, account: Account) -> Account | None:
        """Persist an allowed account status transition with a state CAS."""
        previous_statuses = _ALLOWED_PREVIOUS_STATUSES.get(account.status)
        if previous_statuses is None:
            raise ValueError("Account cannot transition to the pending state.")

        result = await self._read_scalar(
            update(AccountModel)
            .where(
                AccountModel.id == account.id,
                AccountModel.status.in_(tuple(status.value for status in previous_statuses)),
            )
            .values(
                status=account.status.value,
                updated_at=account.updated_at,
            )
            .returning(AccountModel),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def update_role_snapshot(self, account: Account) -> Account | None:
        """Persist the non-authoritative role snapshot for reconciliation."""
        result = await self._read_scalar(
            update(AccountModel)
            .where(AccountModel.id == account.id)
            .values(
                role_snapshot=(
                    account.role_snapshot.value if account.role_snapshot is not None else None
                ),
                updated_at=account.updated_at,
            )
            .returning(AccountModel),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None
