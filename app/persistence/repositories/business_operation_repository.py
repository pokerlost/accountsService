"""Narrow SQLAlchemy persistence adapter for resumable business operations."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from domain.business_operations import BusinessOperation
from domain.enums import BusinessOperationState, BusinessOperationType
from persistence.database.models import BusinessOperationModel

from .base import SQLAlchemyRepository


class BusinessOperationConflictError(RuntimeError):
    """Indicate reuse of an operation key for a different operation type."""

    def __init__(self) -> None:
        super().__init__("Business operation key conflicts with its registered operation type.")


@dataclass(frozen=True, slots=True)
class BusinessOperationRegistrationResult:
    """Describe whether an idempotent operation was inserted or loaded."""

    operation: BusinessOperation
    created: bool


def _to_domain(model: BusinessOperationModel) -> BusinessOperation:
    """Hydrate a framework-independent business operation from one ORM row."""
    return BusinessOperation.hydrate(
        business_operation_id=model.business_operation_id,
        operation_type=BusinessOperationType(model.operation_type),
        state=BusinessOperationState(model.state),
        account_id=model.account_id,
        attempt_count=model.attempt_count,
        last_error_code=model.last_error_code,
        last_error_at=model.last_error_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class BusinessOperationRepository(SQLAlchemyRepository):
    """Persist idempotency identity and distributed-operation progress."""

    async def register_or_load(
        self,
        operation: BusinessOperation,
    ) -> BusinessOperationRegistrationResult:
        """Atomically insert an operation or load a matching registered key."""
        if (
            operation.state is not BusinessOperationState.PENDING_REMOTE
            or operation.attempt_count != 0
        ):
            raise ValueError("Only a new pending business operation can be registered.")

        insert_result = await self._read_scalar(
            postgresql_insert(BusinessOperationModel)
            .values(
                business_operation_id=operation.business_operation_id,
                operation_type=operation.operation_type.value,
                state=operation.state.value,
                account_id=operation.account_id,
                attempt_count=operation.attempt_count,
                last_error_code=operation.last_error_code,
                last_error_at=operation.last_error_at,
                created_at=operation.created_at,
                updated_at=operation.updated_at,
            )
            .on_conflict_do_nothing(
                index_elements=(BusinessOperationModel.business_operation_id,),
            )
            .returning(BusinessOperationModel),
        )
        inserted = insert_result.one_or_none()
        if inserted is not None:
            return BusinessOperationRegistrationResult(
                operation=_to_domain(inserted),
                created=True,
            )

        existing_result = await self._read_scalar(
            select(BusinessOperationModel)
            .where(
                BusinessOperationModel.business_operation_id == operation.business_operation_id,
            )
            .with_for_update(),
        )
        existing = existing_result.one()
        if existing.operation_type != operation.operation_type.value:
            raise BusinessOperationConflictError

        return BusinessOperationRegistrationResult(
            operation=_to_domain(existing),
            created=False,
        )

    async def get_for_update(
        self,
        business_operation_id: UUID,
    ) -> BusinessOperation | None:
        """Lock and return one operation for coordinated workflow progress."""
        result = await self._read_scalar(
            select(BusinessOperationModel)
            .where(
                BusinessOperationModel.business_operation_id == business_operation_id,
            )
            .with_for_update(),
        )
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None

    async def mark_retryable_error(
        self,
        operation: BusinessOperation,
    ) -> BusinessOperation | None:
        """Atomically record a failed remote attempt that remains retryable."""
        return await self._apply_state_change(
            operation,
            target=BusinessOperationState.RETRYABLE_ERROR,
            allowed_current=(
                BusinessOperationState.PENDING_REMOTE,
                BusinessOperationState.RETRYABLE_ERROR,
            ),
            increment_attempt=True,
            persist_error=True,
        )

    async def mark_remote_applied(
        self,
        operation: BusinessOperation,
    ) -> BusinessOperation | None:
        """Atomically record a successful remote mutation."""
        return await self._apply_state_change(
            operation,
            target=BusinessOperationState.REMOTE_APPLIED,
            allowed_current=(
                BusinessOperationState.PENDING_REMOTE,
                BusinessOperationState.RETRYABLE_ERROR,
            ),
            increment_attempt=True,
            persist_error=False,
        )

    async def mark_completed(
        self,
        operation: BusinessOperation,
    ) -> BusinessOperation | None:
        """Atomically finish local reconciliation after remote application."""
        return await self._apply_state_change(
            operation,
            target=BusinessOperationState.COMPLETED,
            allowed_current=(BusinessOperationState.REMOTE_APPLIED,),
            increment_attempt=False,
            persist_error=False,
        )

    async def mark_blocked(
        self,
        operation: BusinessOperation,
    ) -> BusinessOperation | None:
        """Atomically record a terminal remote-stage outcome."""
        return await self._apply_state_change(
            operation,
            target=BusinessOperationState.BLOCKED,
            allowed_current=(
                BusinessOperationState.PENDING_REMOTE,
                BusinessOperationState.RETRYABLE_ERROR,
            ),
            increment_attempt=True,
            persist_error=True,
        )

    async def _apply_state_change(
        self,
        operation: BusinessOperation,
        *,
        target: BusinessOperationState,
        allowed_current: tuple[BusinessOperationState, ...],
        increment_attempt: bool,
        persist_error: bool,
    ) -> BusinessOperation | None:
        if operation.state is not target:
            raise ValueError("Business operation has not applied the requested domain transition.")

        statement = (
            update(BusinessOperationModel)
            .where(
                BusinessOperationModel.business_operation_id == operation.business_operation_id,
                BusinessOperationModel.state.in_(
                    tuple(state.value for state in allowed_current),
                ),
                or_(
                    BusinessOperationModel.account_id.is_(None),
                    BusinessOperationModel.account_id == operation.account_id,
                ),
            )
            .values(
                state=target.value,
                account_id=operation.account_id,
                updated_at=operation.updated_at,
            )
        )
        if increment_attempt:
            statement = statement.values(
                attempt_count=BusinessOperationModel.attempt_count + 1,
            )
        if persist_error and operation.last_error_code is not None:
            statement = statement.values(
                last_error_code=operation.last_error_code,
                last_error_at=operation.last_error_at,
            )

        result = await self._read_scalar(statement.returning(BusinessOperationModel))
        model = result.one_or_none()
        return _to_domain(model) if model is not None else None
