"""Shared API dependency alias facade."""

from __future__ import annotations

from .database import DatabaseSession
from .resources import (
    ApplicationResourcesDep,
    PasswordServiceDep,
)
from .settings import SettingsDep

__all__ = (
    "ApplicationResourcesDep",
    "DatabaseSession",
    "PasswordServiceDep",
    "SettingsDep",
)
