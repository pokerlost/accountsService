"""accountsService policy for roles assignable to human principals."""

from __future__ import annotations

from typing import Final

from pypokerlost.contracts.authorization import AuthorizationRole

from domain.errors import DomainValidationError

_HUMAN_AUTHORIZATION_ROLES: Final[frozenset[AuthorizationRole]] = frozenset(
    {
        AuthorizationRole.USER,
        AuthorizationRole.SUPPORT,
        AuthorizationRole.MASTER,
    }
)


def validate_human_authorization_role(
    value: object,
    *,
    field_name: str,
) -> None:
    """Require one exact shared role that may belong to a human principal."""
    if value is AuthorizationRole.AUTO:
        raise DomainValidationError(
            f"{field_name} cannot be auto; auto is reserved for service principals."
        )
    if not isinstance(value, AuthorizationRole) or value not in _HUMAN_AUTHORIZATION_ROLES:
        raise DomainValidationError(f"{field_name} is invalid.")
