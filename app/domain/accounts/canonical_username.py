"""Canonical human login identifier value."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from domain.errors import DomainValidationError

_CANONICAL_USERNAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"[a-z0-9_]{3,32}")


@dataclass(frozen=True, slots=True, repr=False)
class CanonicalUsername:
    """Immutable canonical username shared by every account use case."""

    value: str

    def __post_init__(self) -> None:
        """Canonicalize and validate without exposing the submitted value."""
        if not isinstance(self.value, str):
            raise DomainValidationError("Canonical username must be text.")

        stripped_value = self.value.strip()
        if not stripped_value.isascii():
            raise DomainValidationError("Canonical username is invalid.")

        canonical_value = stripped_value.lower()
        if _CANONICAL_USERNAME_PATTERN.fullmatch(canonical_value) is None:
            raise DomainValidationError("Canonical username is invalid.")

        object.__setattr__(self, "value", canonical_value)

    def __str__(self) -> str:
        """Return the canonical persistence and comparison representation."""
        return self.value

    def __repr__(self) -> str:
        """Avoid placing a submitted login identifier in diagnostic representations."""
        return "CanonicalUsername(<redacted>)"
