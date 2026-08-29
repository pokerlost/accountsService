"""Small Typer interface for local service startup."""

from __future__ import annotations

import secrets
from time import perf_counter
from typing import Annotated

import typer
import uvicorn

from application.security import Argon2PasswordService
from configuration import Settings
from service import SERVICE_NAME, SERVICE_SLUG

cli = typer.Typer(
    name=SERVICE_SLUG,
    help=f"Run the {SERVICE_NAME} service locally.",
    no_args_is_help=True,
)


@cli.callback()
def operator_cli() -> None:
    """Expose development and service-owned operator commands."""


@cli.command()
def run(
    host: Annotated[
        str | None,
        typer.Option(help="HTTP bind host override."),
    ] = None,
    port: Annotated[
        int | None,
        typer.Option(min=1, max=65535, help="HTTP bind port override."),
    ] = None,
    reload: Annotated[
        bool,
        typer.Option(help="Reload the local server when source files change."),
    ] = False,
) -> None:
    """Start one local Uvicorn development worker."""
    settings = Settings()
    uvicorn.run(
        "api.application:create_app",
        factory=True,
        host=host if host is not None else settings.http.host,
        port=port if port is not None else settings.http.port,
        workers=1,
        reload=reload,
        access_log=False,
    )


@cli.command()
def benchmark_password() -> None:
    """Measure the configured password policy without printing sensitive values."""
    settings = Settings()
    password = secrets.token_urlsafe(24)

    setup_started_at = perf_counter()
    password_service = Argon2PasswordService(settings.password)
    setup_elapsed_ms = (perf_counter() - setup_started_at) * 1_000

    hash_started_at = perf_counter()
    password_hash = password_service.hash_password(password)
    hash_elapsed_ms = (perf_counter() - hash_started_at) * 1_000

    verify_started_at = perf_counter()
    verified = password_service.verify_password(password, password_hash)
    verify_elapsed_ms = (perf_counter() - verify_started_at) * 1_000

    dummy_started_at = perf_counter()
    password_service.verify_dummy(password)
    dummy_elapsed_ms = (perf_counter() - dummy_started_at) * 1_000

    if not verified:
        raise RuntimeError("Password benchmark verification failed")
    typer.echo(f"argon2id dummy setup: {setup_elapsed_ms:.1f} ms")
    typer.echo(f"argon2id hash: {hash_elapsed_ms:.1f} ms")
    typer.echo(f"argon2id verify: {verify_elapsed_ms:.1f} ms")
    typer.echo(f"argon2id dummy verify: {dummy_elapsed_ms:.1f} ms")
