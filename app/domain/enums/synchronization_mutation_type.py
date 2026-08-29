"""Human principal synchronization mutation category."""

from __future__ import annotations

from enum import StrEnum


class SynchronizationMutationType(StrEnum):
    """Supported remote synchronization mutations."""

    SET_STATUS = "set_status"
    ASSIGN_ROLE = "assign_role"
