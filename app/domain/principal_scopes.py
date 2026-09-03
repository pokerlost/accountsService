"""Validation for exact principal scope sets persisted by account workflows."""

from __future__ import annotations

from collections.abc import Iterable

from domain.enums import Scopes
from domain.errors import DomainValidationError


def canonicalize_principal_scopes(
    values: Iterable[Scopes],
    *,
    field_name: str,
) -> tuple[Scopes, ...]:
    """Return a stable tuple of unique global scope members, including an empty set."""
    try:
        scopes = tuple(values)
    except TypeError:
        raise DomainValidationError(
            f"{field_name} must be an iterable of Pokerlost scopes."
        ) from None
    if any(not isinstance(scope, Scopes) for scope in scopes):
        raise DomainValidationError(f"{field_name} contains an invalid Pokerlost scope.")
    if len(frozenset(scopes)) != len(scopes):
        raise DomainValidationError(f"{field_name} must not contain duplicate scopes.")
    return tuple(sorted(scopes, key=lambda scope: scope.value))
