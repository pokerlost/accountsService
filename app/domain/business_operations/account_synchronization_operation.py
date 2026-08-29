"""Persisted human principal synchronization workflow state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID

from domain.enums import HumanRole, RemotePrincipalStatus, SynchronizationMutationType
from domain.errors import DomainValidationError


def _validate_timestamp(value: datetime, *, name: str) -> None:
    """Require a timezone-aware synchronization timestamp."""
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{name} must be a timezone-aware datetime.")


@dataclass(slots=True, init=False)
class AccountSynchronizationOperation:
    """Exactly one desired remote status or role mutation."""

    _business_operation_id: UUID
    _account_id: UUID
    _mutation_type: SynchronizationMutationType
    _desired_status: RemotePrincipalStatus | None
    _desired_role: HumanRole | None
    _created_at: datetime
    _updated_at: datetime

    def __init__(self) -> None:
        """Prevent construction that bypasses mutation-shape validation."""
        raise TypeError(
            "Use AccountSynchronizationOperation.create() or "
            "AccountSynchronizationOperation.hydrate()."
        )

    @classmethod
    def create(
        cls,
        *,
        business_operation_id: UUID,
        account_id: UUID,
        mutation_type: SynchronizationMutationType,
        created_at: datetime,
        desired_status: RemotePrincipalStatus | None = None,
        desired_role: HumanRole | None = None,
    ) -> Self:
        """Create one validated synchronization request."""
        return cls._build(
            business_operation_id=business_operation_id,
            account_id=account_id,
            mutation_type=mutation_type,
            desired_status=desired_status,
            desired_role=desired_role,
            created_at=created_at,
            updated_at=created_at,
        )

    @classmethod
    def hydrate(
        cls,
        *,
        business_operation_id: UUID,
        account_id: UUID,
        mutation_type: SynchronizationMutationType,
        desired_status: RemotePrincipalStatus | None,
        desired_role: HumanRole | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        """Restore one persisted synchronization request."""
        return cls._build(
            business_operation_id=business_operation_id,
            account_id=account_id,
            mutation_type=mutation_type,
            desired_status=desired_status,
            desired_role=desired_role,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def _build(
        cls,
        *,
        business_operation_id: UUID,
        account_id: UUID,
        mutation_type: SynchronizationMutationType,
        desired_status: RemotePrincipalStatus | None,
        desired_role: HumanRole | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        if not isinstance(business_operation_id, UUID):
            raise DomainValidationError("Business operation id must be a UUID.")
        if not isinstance(account_id, UUID):
            raise DomainValidationError("Synchronization account id must be a UUID.")
        if not isinstance(mutation_type, SynchronizationMutationType):
            raise DomainValidationError("Synchronization mutation type is invalid.")
        if desired_status is not None and not isinstance(desired_status, RemotePrincipalStatus):
            raise DomainValidationError("Desired remote principal status is invalid.")
        if desired_role is not None and not isinstance(desired_role, HumanRole):
            raise DomainValidationError("Desired human role is invalid.")
        valid_shape = (
            mutation_type is SynchronizationMutationType.SET_STATUS
            and desired_status is not None
            and desired_role is None
        ) or (
            mutation_type is SynchronizationMutationType.ASSIGN_ROLE
            and desired_role is not None
            and desired_status is None
        )
        if not valid_shape:
            raise DomainValidationError("Synchronization mutation fields have an invalid shape.")
        _validate_timestamp(created_at, name="Synchronization creation time")
        _validate_timestamp(updated_at, name="Synchronization update time")

        operation = object.__new__(cls)
        operation._business_operation_id = business_operation_id
        operation._account_id = account_id
        operation._mutation_type = mutation_type
        operation._desired_status = desired_status
        operation._desired_role = desired_role
        operation._created_at = created_at
        operation._updated_at = updated_at
        return operation

    @property
    def business_operation_id(self) -> UUID:
        """Return the parent idempotent business operation id."""
        return self._business_operation_id

    @property
    def account_id(self) -> UUID:
        """Return the local account whose remote state must change."""
        return self._account_id

    @property
    def mutation_type(self) -> SynchronizationMutationType:
        """Return the exact remote mutation category."""
        return self._mutation_type

    @property
    def desired_status(self) -> RemotePrincipalStatus | None:
        """Return the desired status for a set-status mutation."""
        return self._desired_status

    @property
    def desired_role(self) -> HumanRole | None:
        """Return the desired role for an assign-role mutation."""
        return self._desired_role

    @property
    def created_at(self) -> datetime:
        """Return the timezone-aware workflow creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Return the timezone-aware workflow update timestamp."""
        return self._updated_at
