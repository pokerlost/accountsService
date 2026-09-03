"""Persisted human principal provisioning workflow state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID

from pypokerlost.enums import PrincipalStatus

from domain.enums import Scopes
from domain.errors import DomainConflictError, DomainValidationError
from domain.principal_scopes import canonicalize_principal_scopes


def _validate_timestamp(value: datetime, *, name: str) -> None:
    """Require a timezone-aware provisioning timestamp."""
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{name} must be a timezone-aware datetime.")


@dataclass(slots=True, init=False)
class AccountProvisioningOperation:
    """Minimal resumable state for provisioning one human principal."""

    _business_operation_id: UUID
    _account_id: UUID
    _initial_scopes: tuple[Scopes, ...]
    _remote_principal_id: UUID | None
    _remote_principal_status: PrincipalStatus | None
    _created_at: datetime
    _updated_at: datetime

    def __init__(self) -> None:
        """Prevent construction that bypasses workflow validation."""
        raise TypeError(
            "Use AccountProvisioningOperation.create() or AccountProvisioningOperation.hydrate()."
        )

    @classmethod
    def create(
        cls,
        *,
        business_operation_id: UUID,
        account_id: UUID,
        initial_scopes: tuple[Scopes, ...],
        created_at: datetime,
    ) -> Self:
        """Create a provisioning workflow before any remote result exists."""
        return cls._build(
            business_operation_id=business_operation_id,
            account_id=account_id,
            initial_scopes=initial_scopes,
            remote_principal_id=None,
            remote_principal_status=None,
            created_at=created_at,
            updated_at=created_at,
        )

    @classmethod
    def hydrate(
        cls,
        *,
        business_operation_id: UUID,
        account_id: UUID,
        initial_scopes: tuple[Scopes, ...],
        remote_principal_id: UUID | None,
        remote_principal_status: PrincipalStatus | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        """Restore a persisted provisioning workflow."""
        return cls._build(
            business_operation_id=business_operation_id,
            account_id=account_id,
            initial_scopes=initial_scopes,
            remote_principal_id=remote_principal_id,
            remote_principal_status=remote_principal_status,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def _build(
        cls,
        *,
        business_operation_id: UUID,
        account_id: UUID,
        initial_scopes: tuple[Scopes, ...],
        remote_principal_id: UUID | None,
        remote_principal_status: PrincipalStatus | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> Self:
        if not isinstance(business_operation_id, UUID):
            raise DomainValidationError("Business operation id must be a UUID.")
        if not isinstance(account_id, UUID):
            raise DomainValidationError("Provisioning account id must be a UUID.")
        canonical_scopes = canonicalize_principal_scopes(
            initial_scopes,
            field_name="Initial principal scopes",
        )
        if remote_principal_id is not None and not isinstance(remote_principal_id, UUID):
            raise DomainValidationError("Remote principal id must be a UUID when set.")
        if remote_principal_status is not None and not isinstance(
            remote_principal_status, PrincipalStatus
        ):
            raise DomainValidationError("Remote principal status is invalid.")
        if (remote_principal_id is None) != (remote_principal_status is None):
            raise DomainValidationError("Remote principal id and status must be recorded together.")
        _validate_timestamp(created_at, name="Provisioning creation time")
        _validate_timestamp(updated_at, name="Provisioning update time")

        operation = object.__new__(cls)
        operation._business_operation_id = business_operation_id
        operation._account_id = account_id
        operation._initial_scopes = canonical_scopes
        operation._remote_principal_id = remote_principal_id
        operation._remote_principal_status = remote_principal_status
        operation._created_at = created_at
        operation._updated_at = updated_at
        return operation

    @property
    def business_operation_id(self) -> UUID:
        """Return the parent idempotent business operation id."""
        return self._business_operation_id

    @property
    def account_id(self) -> UUID:
        """Return the local account being provisioned."""
        return self._account_id

    @property
    def initial_scopes(self) -> tuple[Scopes, ...]:
        """Return the exact initial scope set requested for the principal."""
        return self._initial_scopes

    @property
    def remote_principal_id(self) -> UUID | None:
        """Return the provisioned authService principal id when known."""
        return self._remote_principal_id

    @property
    def remote_principal_status(self) -> PrincipalStatus | None:
        """Return the last recorded remote principal status."""
        return self._remote_principal_status

    @property
    def created_at(self) -> datetime:
        """Return the timezone-aware workflow creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Return the timezone-aware workflow update timestamp."""
        return self._updated_at

    def record_remote_result(
        self,
        remote_principal_id: UUID,
        remote_principal_status: PrincipalStatus,
        updated_at: datetime,
    ) -> None:
        """Record a remote result without permitting principal identity replacement."""
        if not isinstance(remote_principal_id, UUID):
            raise DomainValidationError("Remote principal id must be a UUID.")
        if not isinstance(remote_principal_status, PrincipalStatus):
            raise DomainValidationError("Remote principal status is invalid.")
        _validate_timestamp(updated_at, name="Provisioning update time")
        if (
            self._remote_principal_id is not None
            and self._remote_principal_id != remote_principal_id
        ):
            raise DomainConflictError("Provisioning result is bound to another remote principal.")

        self._remote_principal_id = remote_principal_id
        self._remote_principal_status = remote_principal_status
        self._updated_at = updated_at
