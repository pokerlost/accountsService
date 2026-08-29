"""Safe domain error categories."""

from __future__ import annotations


class DomainError(Exception):
    """Base for expected domain failures with safe messages."""


class DomainValidationError(DomainError):
    """A supplied value violates a domain invariant."""


class DomainConflictError(DomainError):
    """A requested mutation conflicts with established domain state."""


class InvalidStateTransitionError(DomainConflictError):
    """A requested lifecycle transition is not permitted."""

    def __init__(self) -> None:
        """Create an error without embedding entity state or submitted values."""
        super().__init__("Domain state transition is not allowed.")
