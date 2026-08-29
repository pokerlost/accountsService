"""Mutable human display nickname value."""

from __future__ import annotations

from dataclasses import dataclass

from domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True, repr=False)
class Nickname:
    """Immutable validated value assigned mutably by an account entity."""

    value: str

    def __post_init__(self) -> None:
        """Strip and validate a Unicode nickname without exposing rejected input."""
        if not isinstance(self.value, str):
            raise DomainValidationError("Nickname must be text.")

        canonical_value = self.value.strip()
        if not 1 <= len(canonical_value) <= 64:
            raise DomainValidationError("Nickname must contain between 1 and 64 characters.")

        object.__setattr__(self, "value", canonical_value)

    def __str__(self) -> str:
        """Return the normalized persistence representation."""
        return self.value

    def __repr__(self) -> str:
        """Avoid placing a submitted display value in validation diagnostics."""
        return "Nickname(<redacted>)"
