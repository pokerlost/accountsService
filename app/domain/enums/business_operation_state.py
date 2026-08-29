"""Resumable business operation lifecycle state."""

from __future__ import annotations

from enum import StrEnum


class BusinessOperationState(StrEnum):
    """Persisted progress states for one distributed mutation."""

    PENDING_REMOTE = "pending_remote"
    RETRYABLE_ERROR = "retryable_error"
    REMOTE_APPLIED = "remote_applied"
    COMPLETED = "completed"
    BLOCKED = "blocked"
