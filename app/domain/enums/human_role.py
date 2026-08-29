"""Non-authoritative human role snapshot values."""

from __future__ import annotations

from enum import StrEnum


class HumanRole(StrEnum):
    """Roles that may be associated with human principals."""

    USER = "user"
    SUPPORT = "support"
    MASTER = "master"
