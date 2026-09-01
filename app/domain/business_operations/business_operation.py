"""Resumable distributed business operation aggregate."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Self
from uuid import UUID

from domain.enums import BusinessOperationState, BusinessOperationType
from domain.errors import (
    DomainConflictError,
    DomainValidationError,
    InvalidStateTransitionError,
)

_ERROR_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
_ALLOWED_STATE_TRANSITIONS: Final[
    dict[BusinessOperationState, frozenset[BusinessOperationState]]
] = {
    BusinessOperationState.PENDING_REMOTE: frozenset(
        {
            BusinessOperationState.RETRYABLE_ERROR,
            BusinessOperationState.REMOTE_APPLIED,
            BusinessOperationState.BLOCKED,
        }
    ),
    BusinessOperationState.RETRYABLE_ERROR: frozenset(
        {
            BusinessOperationState.REMOTE_APPLIED,
            BusinessOperationState.BLOCKED,
        }
    ),
    BusinessOperationState.REMOTE_APPLIED: frozenset({BusinessOperationState.COMPLETED}),
    BusinessOperationState.COMPLETED: frozenset(),
    BusinessOperationState.BLOCKED: frozenset(),
}


def _validate_timestamp(value: datetime, *, name: str) -> None:
    """Require a timezone-aware operation timestamp."""
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{name} must be a timezone-aware datetime.")


def _validate_error(error_code: str | None, error_at: datetime | None) -> None:
    """Require complete, safe last-error metadata when present."""
    if (error_code is None) != (error_at is None):
        raise DomainValidationError("Last-error code and timestamp must be set together.")
    if error_code is not None and (
        not isinstance(error_code, str) or _ERROR_CODE_PATTERN.fullmatch(error_code) is None
    ):
        raise DomainValidationError("Last-error code must be a bounded categorical value.")
    if error_at is not None:
        _validate_timestamp(error_at, name="Last-error time")


@dataclass(slots=True, init=False)
class BusinessOperation:
    """Idempotent operation key and controlled distributed workflow state."""

    _business_operation_id: UUID
    _operation_type: BusinessOperationType
    _state: BusinessOperationState
    _account_id: UUID | None
    _attempt_count: int
    _last_error_code: str | None
    _last_error_at: datetime | None
    _created_at: datetime
    _updated_at: datetime

    def __init__(self) -> None:
        """Prevent construction that bypasses identity and state validation."""
        raise TypeError("Use BusinessOperation.create() or BusinessOperation.hydrate().")

    @classmethod
    def create(
        cls,
        *,
        business_operation_id: UUID,
        operation_type: BusinessOperationType,
        created_at: datetime,
        account_id: UUID | None = None,
    ) -> Self:
        """Create a newly registered operation awaiting its remote mutation."""
        return cls._build(
            business_operation_id=business_operation_id,
            operation_type=operation_type,
            state=BusinessOperationState.PENDING_REMOTE,
            account_id=account_id,
            attempt_count=0,
            last_error_code=None,
            last_error_at=None,
            created_at=created_at,
            updated_at=created_at,
        )

    @classmethod
    def hydrate(
        cls,
        *,
        business_operation_id: UUID,
        operation_type: BusinessOperationType,
        state: BusinessOperationState,
        account_id: UUID | None,
        attempt_count: int,
        last_error_code: str | None,
        last_error_at: datetime | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        """Restore a persisted operation while rechecking all safe invariants."""
        return cls._build(
            business_operation_id=business_operation_id,
            operation_type=operation_type,
            state=state,
            account_id=account_id,
            attempt_count=attempt_count,
            last_error_code=last_error_code,
            last_error_at=last_error_at,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def _build(
        cls,
        *,
        business_operation_id: UUID,
        operation_type: BusinessOperationType,
        state: BusinessOperationState,
        account_id: UUID | None,
        attempt_count: int,
        last_error_code: str | None,
        last_error_at: datetime | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        if not isinstance(business_operation_id, UUID):
            raise DomainValidationError("Business operation id must be a UUID.")
        if not isinstance(operation_type, BusinessOperationType):
            raise DomainValidationError("Business operation type is invalid.")
        if not isinstance(state, BusinessOperationState):
            raise DomainValidationError("Business operation state is invalid.")
        if account_id is not None and not isinstance(account_id, UUID):
            raise DomainValidationError("Operation account id must be a UUID when set.")
        if (
            not isinstance(attempt_count, int)
            or isinstance(attempt_count, bool)
            or attempt_count < 0
        ):
            raise DomainValidationError("Attempt count must be a non-negative integer.")
        _validate_error(last_error_code, last_error_at)
        _validate_timestamp(created_at, name="Operation creation time")
        _validate_timestamp(updated_at, name="Operation update time")

        operation = object.__new__(cls)
        operation._business_operation_id = business_operation_id
        operation._operation_type = operation_type
        operation._state = state
        operation._account_id = account_id
        operation._attempt_count = attempt_count
        operation._last_error_code = last_error_code
        operation._last_error_at = last_error_at
        operation._created_at = created_at
        operation._updated_at = updated_at
        return operation

    @property
    def business_operation_id(self) -> UUID:
        """Return the caller-supplied idempotency key."""
        return self._business_operation_id

    @property
    def operation_type(self) -> BusinessOperationType:
        """Return the distributed mutation category."""
        return self._operation_type

    @property
    def state(self) -> BusinessOperationState:
        """Return the persisted workflow state."""
        return self._state

    @property
    def account_id(self) -> UUID | None:
        """Return the associated local account when established."""
        return self._account_id

    @property
    def attempt_count(self) -> int:
        """Return the number of recorded remote attempts."""
        return self._attempt_count

    @property
    def last_error_code(self) -> str | None:
        """Return the last safe categorical failure code."""
        return self._last_error_code

    @property
    def last_error_at(self) -> datetime | None:
        """Return when the last categorical failure occurred."""
        return self._last_error_at

    @property
    def created_at(self) -> datetime:
        """Return the timezone-aware registration timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Return the timezone-aware last-update timestamp."""
        return self._updated_at

    def bind_account(self, account_id: UUID, updated_at: datetime) -> None:
        """Associate the operation with one immutable local account identity."""
        if not isinstance(account_id, UUID):
            raise DomainValidationError("Operation account id must be a UUID.")
        _validate_timestamp(updated_at, name="Operation update time")
        if self._account_id is not None:
            if self._account_id == account_id:
                return
            raise DomainConflictError("Business operation is already associated with an account.")

        self._account_id = account_id
        self._updated_at = updated_at

    def mark_retryable_error(self, error_code: str, error_at: datetime) -> None:
        """Record one failed remote attempt that may safely be resumed."""
        _validate_error(error_code, error_at)
        if self._state is not BusinessOperationState.RETRYABLE_ERROR:
            self._transition_to(BusinessOperationState.RETRYABLE_ERROR)
        self._attempt_count += 1
        self._last_error_code = error_code
        self._last_error_at = error_at
        self._updated_at = error_at

    def mark_remote_applied(self, updated_at: datetime) -> None:
        """Record one successful remote mutation while retaining prior failure metadata."""
        _validate_timestamp(updated_at, name="Operation update time")
        self._transition_to(BusinessOperationState.REMOTE_APPLIED)
        self._attempt_count += 1
        self._updated_at = updated_at

    def mark_completed(self, updated_at: datetime) -> None:
        """Mark locally reconciled state as complete."""
        _validate_timestamp(updated_at, name="Operation update time")
        self._transition_to(BusinessOperationState.COMPLETED)
        self._updated_at = updated_at

    def mark_blocked(
        self,
        updated_at: datetime,
        *,
        error_code: str | None = None,
    ) -> None:
        """Terminate a remote-stage operation that cannot be retried automatically."""
        _validate_timestamp(updated_at, name="Operation update time")
        if error_code is not None:
            _validate_error(error_code, updated_at)
        self._transition_to(BusinessOperationState.BLOCKED)
        self._attempt_count += 1
        if error_code is not None:
            self._last_error_code = error_code
            self._last_error_at = updated_at
        self._updated_at = updated_at

    def _transition_to(self, target: BusinessOperationState) -> None:
        if target not in _ALLOWED_STATE_TRANSITIONS[self._state]:
            raise InvalidStateTransitionError()
        self._state = target
