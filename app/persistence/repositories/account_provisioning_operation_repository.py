"""SQLAlchemy persistence adapter for account provisioning workflows."""

from __future__ import annotations

from uuid import UUID

from pypokerlost.contracts.authorization import AuthorizationRole, PrincipalStatus
from sqlalchemy import and_, insert, or_, select, update

from domain.business_operations import AccountProvisioningOperation
from persistence.database.models import AccountProvisioningOperationModel

from .base import SQLAlchemyRepository


class ProvisioningRemoteResultConflictError(RuntimeError):
    """Indicate an attempted replacement of a recorded remote principal."""

    def __init__(self) -> None:
        super().__init__("Provisioning result conflicts with the recorded remote principal.")


def _to_domain(model: AccountProvisioningOperationModel) -> AccountProvisioningOperation:
    """Hydrate a provisioning workflow from one ORM row."""
    return AccountProvisioningOperation.hydrate(
        business_operation_id=model.business_operation_id,
        account_id=model.account_id,
        requested_role=AuthorizationRole(model.requested_role),
        remote_principal_id=model.remote_principal_id,
        remote_principal_status=(
            PrincipalStatus(model.remote_principal_status)
            if model.remote_principal_status is not None
            else None
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class AccountProvisioningOperationRepository(SQLAlchemyRepository):
    """Persist resumable state for one human-principal provisioning workflow."""

    async def add(
        self,
        operation: AccountProvisioningOperation,
    ) -> AccountProvisioningOperation:
        """Insert and return one provisioning workflow."""
        result = await self._read_scalar(
            insert(AccountProvisioningOperationModel)
            .values(
                business_operation_id=operation.business_operation_id,
                account_id=operation.account_id,
                requested_role=operation.requested_role.value,
                remote_principal_id=operation.remote_principal_id,
                remote_principal_status=(
                    operation.remote_principal_status.value
                    if operation.remote_principal_status is not None
                    else None
                ),
                created_at=operation.created_at,
                updated_at=operation.updated_at,
            )
            .returning(AccountProvisioningOperationModel),
        )
        return _to_domain(result.one())

    async def get_by_business_operation_id(
        self,
        business_operation_id: UUID,
    ) -> AccountProvisioningOperation | None:
        """Return one provisioning workflow by its parent operation id."""
        result = await self._read_scalar(
            select(AccountProvisioningOperationModel).where(
                AccountProvisioningOperationModel.business_operation_id == business_operation_id,
            ),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def record_remote_result(
        self,
        operation: AccountProvisioningOperation,
    ) -> AccountProvisioningOperation | None:
        """Persist a remote result idempotently without replacing its principal id."""
        if operation.remote_principal_id is None or operation.remote_principal_status is None:
            raise ValueError("A complete remote provisioning result is required.")

        result = await self._read_scalar(
            update(AccountProvisioningOperationModel)
            .where(
                AccountProvisioningOperationModel.business_operation_id
                == operation.business_operation_id,
                or_(
                    AccountProvisioningOperationModel.remote_principal_id.is_(None),
                    and_(
                        AccountProvisioningOperationModel.remote_principal_id
                        == operation.remote_principal_id,
                        AccountProvisioningOperationModel.updated_at <= operation.updated_at,
                    ),
                ),
            )
            .values(
                remote_principal_id=operation.remote_principal_id,
                remote_principal_status=operation.remote_principal_status.value,
                updated_at=operation.updated_at,
            )
            .returning(AccountProvisioningOperationModel),
        )
        model = result.one_or_none()
        if model is not None:
            return _to_domain(model)

        existing_result = await self._read_scalar(
            select(AccountProvisioningOperationModel)
            .where(
                AccountProvisioningOperationModel.business_operation_id
                == operation.business_operation_id,
            )
            .with_for_update(),
        )
        existing = existing_result.one_or_none()
        if existing is None:
            return None
        if existing.remote_principal_id != operation.remote_principal_id:
            raise ProvisioningRemoteResultConflictError
        return _to_domain(existing)
