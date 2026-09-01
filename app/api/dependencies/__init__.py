"""Shared API dependency alias facade."""

from __future__ import annotations

from .authorization import (
    PokerlostTokenVerifierDep,
    authorize_pokerlost_request,
)
from .database import DatabaseSession
from .resources import ApplicationResourcesDep, PasswordServiceDep
from .settings import SettingsDep

__all__ = (
    "ApplicationResourcesDep",
    "DatabaseSession",
    "PasswordServiceDep",
    "PokerlostTokenVerifierDep",
    "SettingsDep",
    "authorize_pokerlost_request",
)
