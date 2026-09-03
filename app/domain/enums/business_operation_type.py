"""Resumable business operation categories."""

from __future__ import annotations

from enum import StrEnum


class BusinessOperationType(StrEnum):
    """Distributed mutations persisted by accountsService."""

    REGISTER = "register"
    CREATE_STAFF = "create_staff"
    DISABLE = "disable"
    ENABLE = "enable"
    REPLACE_SCOPES = "replace_scopes"
