"""Human account aggregate lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final, Self
from uuid import UUID

from pypokerlost.types import AuthorizationRole

from domain.enums import AccountStatus
from domain.errors import (
    DomainConflictError,
    DomainValidationError,
    InvalidStateTransitionError,
)
from domain.human_role_policy import validate_human_authorization_role

from .canonical_username import CanonicalUsername
from .nickname import Nickname

_ALLOWED_STATUS_TRANSITIONS: Final[dict[AccountStatus, frozenset[AccountStatus]]] = {
    AccountStatus.PENDING: frozenset({AccountStatus.ACTIVE}),
    AccountStatus.ACTIVE: frozenset({AccountStatus.DISABLED}),
    AccountStatus.DISABLED: frozenset({AccountStatus.ACTIVE}),
}


def _validate_timestamp(value: datetime, *, name: str) -> None:
    """Require a timezone-aware domain timestamp."""
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{name} must be a timezone-aware datetime.")


@dataclass(slots=True, init=False)
class Account:
    """Human account with mutations restricted to explicit domain operations."""

    _id: UUID
    _auth_principal_id: UUID | None
    _username: CanonicalUsername
    _nickname: Nickname
    _status: AccountStatus
    _role_snapshot: AuthorizationRole | None
    _created_at: datetime
    _updated_at: datetime

    def __init__(self) -> None:
        """Prevent construction that bypasses the new and hydration paths."""
        raise TypeError("Use Account.new() or Account.hydrate().")

    @classmethod
    def new(
        cls,
        *,
        id: UUID,
        username: CanonicalUsername,
        nickname: Nickname,
        created_at: datetime,
        role_snapshot: AuthorizationRole | None = None,
    ) -> Self:
        """Create a new local account in the mandatory pending state."""
        return cls._build(
            id=id,
            auth_principal_id=None,
            username=username,
            nickname=nickname,
            status=AccountStatus.PENDING,
            role_snapshot=role_snapshot,
            created_at=created_at,
            updated_at=created_at,
        )

    @classmethod
    def hydrate(
        cls,
        *,
        id: UUID,
        auth_principal_id: UUID | None,
        username: CanonicalUsername,
        nickname: Nickname,
        status: AccountStatus,
        role_snapshot: AuthorizationRole | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        """Restore a persisted account while rechecking all domain invariants."""
        return cls._build(
            id=id,
            auth_principal_id=auth_principal_id,
            username=username,
            nickname=nickname,
            status=status,
            role_snapshot=role_snapshot,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def _build(
        cls,
        *,
        id: UUID,
        auth_principal_id: UUID | None,
        username: CanonicalUsername,
        nickname: Nickname,
        status: AccountStatus,
        role_snapshot: AuthorizationRole | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        if not isinstance(id, UUID):
            raise DomainValidationError("Account id must be a UUID.")
        if auth_principal_id is not None and not isinstance(auth_principal_id, UUID):
            raise DomainValidationError("Authentication principal id must be a UUID when set.")
        if not isinstance(username, CanonicalUsername):
            raise DomainValidationError("Account username must be canonical.")
        if not isinstance(nickname, Nickname):
            raise DomainValidationError("Account nickname must be validated.")
        if not isinstance(status, AccountStatus):
            raise DomainValidationError("Account status is invalid.")
        if role_snapshot is not None:
            validate_human_authorization_role(
                role_snapshot,
                field_name="Human role snapshot",
            )
        if status is not AccountStatus.PENDING and auth_principal_id is None:
            raise DomainValidationError(
                "A non-pending account requires an authentication principal."
            )
        _validate_timestamp(created_at, name="Account creation time")
        _validate_timestamp(updated_at, name="Account update time")

        account = object.__new__(cls)
        account._id = id
        account._auth_principal_id = auth_principal_id
        account._username = username
        account._nickname = nickname
        account._status = status
        account._role_snapshot = role_snapshot
        account._created_at = created_at
        account._updated_at = updated_at
        return account

    @property
    def id(self) -> UUID:
        """Return the stable local account identifier."""
        return self._id

    @property
    def auth_principal_id(self) -> UUID | None:
        """Return the bound authService principal identifier when available."""
        return self._auth_principal_id

    @property
    def username(self) -> CanonicalUsername:
        """Return the immutable canonical login identifier."""
        return self._username

    @property
    def nickname(self) -> Nickname:
        """Return the current display nickname."""
        return self._nickname

    @property
    def status(self) -> AccountStatus:
        """Return the current local lifecycle state."""
        return self._status

    @property
    def role_snapshot(self) -> AuthorizationRole | None:
        """Return the reconciliation-only human role snapshot."""
        return self._role_snapshot

    @property
    def created_at(self) -> datetime:
        """Return the timezone-aware creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Return the timezone-aware last-update timestamp."""
        return self._updated_at

    def bind_auth_principal(self, auth_principal_id: UUID, updated_at: datetime) -> None:
        """Bind one immutable remote principal identity, idempotently for the same value."""
        if not isinstance(auth_principal_id, UUID):
            raise DomainValidationError("Authentication principal id must be a UUID.")
        _validate_timestamp(updated_at, name="Account update time")
        if self._auth_principal_id is not None:
            if self._auth_principal_id == auth_principal_id:
                return
            raise DomainConflictError(
                "Account is already bound to another authentication principal."
            )

        self._auth_principal_id = auth_principal_id
        self._updated_at = updated_at

    def update_nickname(self, nickname: Nickname, updated_at: datetime) -> None:
        """Replace the non-unique display nickname."""
        if not isinstance(nickname, Nickname):
            raise DomainValidationError("Account nickname must be validated.")
        _validate_timestamp(updated_at, name="Account update time")
        self._nickname = nickname
        self._updated_at = updated_at

    def transition_status(self, status: AccountStatus, updated_at: datetime) -> None:
        """Apply one explicitly permitted lifecycle transition."""
        if not isinstance(status, AccountStatus):
            raise DomainValidationError("Account status is invalid.")
        _validate_timestamp(updated_at, name="Account update time")
        if status not in _ALLOWED_STATUS_TRANSITIONS[self._status]:
            raise InvalidStateTransitionError()
        if self._auth_principal_id is None:
            raise DomainConflictError("Account activation requires an authentication principal.")

        self._status = status
        self._updated_at = updated_at

    def update_role_snapshot(
        self,
        role_snapshot: AuthorizationRole | None,
        updated_at: datetime,
    ) -> None:
        """Replace or clear the informational role snapshot."""
        if role_snapshot is not None:
            validate_human_authorization_role(
                role_snapshot,
                field_name="Human role snapshot",
            )
        _validate_timestamp(updated_at, name="Account update time")
        self._role_snapshot = role_snapshot
        self._updated_at = updated_at
