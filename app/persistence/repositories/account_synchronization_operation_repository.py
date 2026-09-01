"""SQLAlchemy persistence adapter for account synchronization workflows."""

from __future__ import annotations

from uuid import UUID

from pypokerlost.types import AuthorizationRole, PrincipalStatus
from sqlalchemy import insert, select

from domain.business_operations import AccountSynchronizationOperation
from domain.enums import SynchronizationMutationType
from persistence.database.models import AccountSynchronizationOperationModel

from .base import SQLAlchemyRepository


def _to_domain(model: AccountSynchronizationOperationModel) -> AccountSynchronizationOperation:
    """Hydrate a synchronization workflow from one ORM row."""
    return AccountSynchronizationOperation.hydrate(
        business_operation_id=model.business_operation_id,
        account_id=model.account_id,
        mutation_type=SynchronizationMutationType(model.mutation_type),
        desired_status=(
            PrincipalStatus(model.desired_status) if model.desired_status is not None else None
        ),
        desired_role=(
            AuthorizationRole(model.desired_role) if model.desired_role is not None else None
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class AccountSynchronizationOperationRepository(SQLAlchemyRepository):
    """Persist one exact desired remote status or role mutation."""

    async def add(
        self,
        operation: AccountSynchronizationOperation,
    ) -> AccountSynchronizationOperation:
        """Insert and return one validated synchronization workflow."""
        result = await self._read_scalar(
            insert(AccountSynchronizationOperationModel)
            .values(
                business_operation_id=operation.business_operation_id,
                account_id=operation.account_id,
                mutation_type=operation.mutation_type.value,
                desired_status=(
                    operation.desired_status.value if operation.desired_status is not None else None
                ),
                desired_role=(
                    operation.desired_role.value if operation.desired_role is not None else None
                ),
                created_at=operation.created_at,
                updated_at=operation.updated_at,
            )
            .returning(AccountSynchronizationOperationModel),
        )
        return _to_domain(result.one())

    async def get_by_business_operation_id(
        self,
        business_operation_id: UUID,
    ) -> AccountSynchronizationOperation | None:
        """Return one synchronization workflow by its parent operation id."""
        result = await self._read_scalar(
            select(AccountSynchronizationOperationModel).where(
                AccountSynchronizationOperationModel.business_operation_id == business_operation_id,
            ),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None
