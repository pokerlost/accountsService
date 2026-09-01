"""Argon2id password hashing, verification and policy-rehash service."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

from configuration.password import PasswordSettings
from domain.accounts import PasswordCredential

type Clock = Callable[..., datetime]


class PasswordPolicyError(ValueError):
    """Password input does not satisfy the service-owned length policy."""

    def __init__(self, *, min_length: int, max_length: int) -> None:
        """Create a validation error that never retains the rejected input."""
        super().__init__(f"Password must contain between {min_length} and {max_length} characters")


def _utc_now() -> datetime:
    """Return the default timezone-aware service timestamp."""
    return datetime.now(UTC)


class Argon2PasswordService:
    """Own one configured Argon2id policy and lifecycle-scoped dummy hash."""

    __slots__ = ("_clock", "_dummy_hash", "_hasher", "_settings")

    def __init__(
        self,
        settings: PasswordSettings,
        *,
        clock: Clock = _utc_now,
    ) -> None:
        """Initialize and pay the dummy-hash setup cost exactly once."""
        self._clock = clock
        self._settings = settings
        self._hasher = PasswordHasher(
            type=Type.ID,
            memory_cost=settings.argon2_memory_cost,
            time_cost=settings.argon2_time_cost,
            parallelism=settings.argon2_parallelism,
            hash_len=settings.argon2_hash_length,
            salt_len=settings.argon2_salt_length,
        )
        self._dummy_hash = self._hasher.hash(secrets.token_urlsafe(32))

    def hash_password(self, password: str) -> str:
        """Validate the exact input and return only its Argon2id PHC string."""
        self._validate_password_input(password)
        return self._hasher.hash(password)

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Return one generic false result for mismatch or malformed stored data."""
        if not isinstance(password, str) or not isinstance(stored_hash, str):
            return False
        try:
            return self._hasher.verify(stored_hash, password)
        except InvalidHashError, VerificationError, UnicodeError:
            return False

    def needs_rehash(self, stored_hash: str) -> bool:
        """Report whether a valid PHC string differs from the configured policy."""
        if not isinstance(stored_hash, str):
            return False
        try:
            return self._hasher.check_needs_rehash(stored_hash)
        except InvalidHashError, VerificationError, UnicodeError:
            return False

    def rehash_after_success(
        self,
        credential: PasswordCredential,
        password: str,
    ) -> bool:
        """Apply a policy-only rehash while preserving password-changed semantics."""
        if not self.needs_rehash(credential.password_hash):
            return False
        self._validate_password_input(password)
        credential.apply_policy_rehash(
            self._hasher.hash(password),
            hash_updated_at=self._aware_now(),
        )
        return True

    def verify_dummy(self, password: str) -> bool:
        """Perform Argon2 work for an unknown account and always return false."""
        candidate = password if isinstance(password, str) else ""
        with suppress(InvalidHashError, VerificationError, UnicodeError):
            self._hasher.verify(self._dummy_hash, candidate)
        return False

    def _aware_now(self) -> datetime:
        timestamp = self._clock()
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Password service clock must return a timezone-aware datetime")
        return timestamp

    def _validate_password_input(self, password: str) -> None:
        if not isinstance(password, str) or not (
            self._settings.min_length <= len(password) <= self._settings.max_length
        ):
            raise PasswordPolicyError(
                min_length=self._settings.min_length,
                max_length=self._settings.max_length,
            )
