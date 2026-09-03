"""Service-owned exact access-token scope catalog."""

from __future__ import annotations

from enum import StrEnum


class Scopes(StrEnum):
    """Stable capabilities owned by accountsService."""

    SELF_GET_ME = "accounts.self.getMe"
    SELF_UPDATE_NICKNAME = "accounts.self.updateNickname"
    ACCOUNT_READ = "accounts.account.read"
    STAFF_CREATE = "accounts.staff.create"
    ACCOUNT_DISABLE = "accounts.account.disable"
    ACCOUNT_ENABLE = "accounts.account.enable"
    ACCOUNT_REPLACE_SCOPES = "accounts.account.replaceScopes"
