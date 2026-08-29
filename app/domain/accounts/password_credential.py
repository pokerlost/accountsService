"""Persisted Argon2id password credential entity."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final, Self
from uuid import UUID

from domain.errors import DomainValidationError

_ARGON2ID_PHC_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\$argon2id\$v=19\$m=[1-9][0-9]*,t=[1-9][0-9]*,p=[1-9][0-9]*\$"
    r"[A-Za-z0-9+/]+={0,2}\$[A-Za-z0-9+/]+={0,2}"
)


def _validate_timestamp(value: datetime, *, name: str) -> None:
    """Require a timezone-aware credential timestamp."""
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{name} must be a timezone-aware datetime.")


def _validate_password_hash(password_hash: str) -> None:
    """Require an Argon2id PHC representation without exposing it on failure."""
    if not isinstance(password_hash, str) or _ARGON2ID_PHC_PATTERN.fullmatch(password_hash) is None:
        raise DomainValidationError("Password credential hash must be a valid Argon2id PHC string.")


@dataclass(slots=True, init=False)
class PasswordCredential:
    """One human account password hash with controlled policy-only rehashing."""

    _account_id: UUID
    _password_hash: str = field(repr=False)
    _password_changed_at: datetime
    _hash_updated_at: datetime

    def __init__(self) -> None:
        """Prevent construction that could skip PHC and timestamp validation."""
        raise TypeError("Use PasswordCredential.create() or PasswordCredential.hydrate().")

    @classmethod
    def create(
        cls,
        *,
        account_id: UUID,
        password_hash: str,
        password_changed_at: datetime,
    ) -> Self:
        """Create an initial credential whose password and hash timestamps coincide."""
        return cls._build(
            account_id=account_id,
            password_hash=password_hash,
            password_changed_at=password_changed_at,
            hash_updated_at=password_changed_at,
        )

    @classmethod
    def hydrate(
        cls,
        *,
        account_id: UUID,
        password_hash: str,
        password_changed_at: datetime,
        hash_updated_at: datetime,
    ) -> Self:
        """Restore a persisted password credential while rechecking safe invariants."""
        return cls._build(
            account_id=account_id,
            password_hash=password_hash,
            password_changed_at=password_changed_at,
            hash_updated_at=hash_updated_at,
        )

    @classmethod
    def _build(
        cls,
        *,
        account_id: UUID,
        password_hash: str,
        password_changed_at: datetime,
        hash_updated_at: datetime,
    ) -> Self:
        if not isinstance(account_id, UUID):
            raise DomainValidationError("Credential account id must be a UUID.")
        _validate_password_hash(password_hash)
        _validate_timestamp(password_changed_at, name="Password change time")
        _validate_timestamp(hash_updated_at, name="Hash update time")
        if hash_updated_at < password_changed_at:
            raise DomainValidationError("Hash update time cannot precede password change time.")

        credential = object.__new__(cls)
        credential._account_id = account_id
        credential._password_hash = password_hash
        credential._password_changed_at = password_changed_at
        credential._hash_updated_at = hash_updated_at
        return credential

    @property
    def account_id(self) -> UUID:
        """Return the owning human account identifier."""
        return self._account_id

    @property
    def password_hash(self) -> str:
        """Return the PHC value only for password and persistence boundaries."""
        return self._password_hash

    @property
    def password_changed_at(self) -> datetime:
        """Return when the user-supplied password last changed."""
        return self._password_changed_at

    @property
    def hash_updated_at(self) -> datetime:
        """Return when the stored policy representation last changed."""
        return self._hash_updated_at

    def apply_policy_rehash(self, password_hash: str, hash_updated_at: datetime) -> None:
        """Replace only the hash representation after successful password verification."""
        _validate_password_hash(password_hash)
        _validate_timestamp(hash_updated_at, name="Hash update time")
        if hash_updated_at < self._hash_updated_at:
            raise DomainValidationError("Hash update time cannot move backwards.")

        self._password_hash = password_hash
        self._hash_updated_at = hash_updated_at
