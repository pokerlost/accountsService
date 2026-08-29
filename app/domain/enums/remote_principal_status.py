"""Remote human principal status snapshot."""

from __future__ import annotations

from enum import StrEnum


class RemotePrincipalStatus(StrEnum):
    """Remote states relevant to accountsService workflows."""

    ACTIVE = "active"
    DISABLED = "disabled"
