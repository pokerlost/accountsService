"""Human account lifecycle status."""

from __future__ import annotations

from enum import StrEnum


class AccountStatus(StrEnum):
    """Supported local human account lifecycle states."""

    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
