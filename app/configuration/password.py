"""Password input and Argon2id policy settings."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from .base import SettingsModel


class PasswordSettings(SettingsModel):
    """Validated deployment policy for password input and Argon2id hashing."""

    argon2_memory_cost: int = Field(
        default=65_536,
        ge=8_192,
        le=1_048_576,
        description="Argon2id memory cost in KiB.",
    )
    argon2_time_cost: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Argon2id iteration count.",
    )
    argon2_parallelism: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Argon2id parallelism degree.",
    )
    argon2_hash_length: int = Field(
        default=32,
        ge=16,
        le=128,
        description="Argon2id derived hash length in bytes.",
    )
    argon2_salt_length: int = Field(
        default=16,
        ge=16,
        le=64,
        description="Argon2id random salt length in bytes.",
    )
    min_length: int = Field(
        default=12,
        ge=1,
        le=1_024,
        description="Minimum accepted password length in Unicode code points.",
    )
    max_length: int = Field(
        default=256,
        ge=1,
        le=4_096,
        description="Maximum accepted password length in Unicode code points.",
    )

    @model_validator(mode="after")
    def validate_length_range(self) -> Self:
        """Require one non-empty, ordered password length interval."""
        if self.min_length > self.max_length:
            raise ValueError("Password minimum length must not exceed maximum length")
        return self
