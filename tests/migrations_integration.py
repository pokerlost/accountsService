"""Historical revisions run only in a database created and owned by this test."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import asyncpg
import pytest
from sqlalchemy.engine import make_url


class MigrationDatabase:
    def __init__(self, url: str) -> None:
        self.url = url

    def query(self, sql: str) -> list[tuple[object, ...]]:
        async def execute() -> list[tuple[object, ...]]:
            connection = await asyncpg.connect(self.url)
            try:
                if sql.lstrip().startswith("SELECT"):
                    return [tuple(row) for row in await connection.fetch(sql)]
                await connection.execute(sql)
                return []
            finally:
                await connection.close()

        return asyncio.run(execute())

    def migrate(
        self, direction: str, revision: str, *, error: str | None = None
    ) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", direction, revision],
            cwd=Path(__file__).resolve().parents[1],
            env={
                **os.environ,
                "DATABASE_URL": self.url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                ),
            },
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if error is None:
            assert result.returncode == 0, result.stdout + result.stderr
        else:
            assert result.returncode != 0
            assert error in result.stderr


@pytest.fixture
def database() -> Iterator[MigrationDatabase]:
    control_url = (
        make_url(os.environ["TEST_DATABASE_URL"])
        .set(drivername="postgresql")
        .render_as_string(hide_password=False)
    )
    # The name contains only this reserved prefix and a locally generated UUID.
    name = "migration_test_" + uuid4().hex

    async def control(sql: str) -> None:
        connection = await asyncpg.connect(control_url)
        try:
            await connection.execute(sql)
        finally:
            await connection.close()

    asyncio.run(control(f'CREATE DATABASE "{name}"'))
    try:
        yield MigrationDatabase(
            make_url(control_url)
            .set(database=name)
            .render_as_string(hide_password=False)
        )
    finally:
        asyncio.run(control(f'DROP DATABASE "{name}" WITH (FORCE)'))


def test_empty_historical_chain_round_trip(database: MigrationDatabase) -> None:
    database.migrate("upgrade", "head")
    assert database.query("SELECT version_num FROM alembic_version") == [
        ("20260903_0003",)
    ]
    database.migrate("downgrade", "base")
    assert database.query(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    ) == [("alembic_version",)]
    database.migrate("upgrade", "head")
    assert database.query("SELECT version_num FROM alembic_version") == [
        ("20260903_0003",)
    ]


@pytest.mark.parametrize(
    "direction, start, operation",
    [
        ("upgrade", "20260901_0002", "assign_role"),
        ("downgrade", "head", "replace_scopes"),
    ],
)
def test_role_or_scope_business_rows_block_lossy_conversion(
    database: MigrationDatabase, direction: str, start: str, operation: str
) -> None:
    database.migrate("upgrade", start)
    database.query(f"""
        INSERT INTO business_operations (business_operation_id, operation_type, state)
        VALUES (gen_random_uuid(), '{operation}', 'pending_remote')
    """)
    before = database.query("SELECT * FROM business_operations")
    revision = "head" if direction == "upgrade" else "20260901_0002"
    database.migrate(direction, revision, error="exact scopes are unavailable")
    assert database.query("SELECT * FROM business_operations") == before
    assert database.query("SELECT version_num FROM alembic_version") == [
        ("20260901_0002" if direction == "upgrade" else "20260903_0003",)
    ]


def test_fingerprint_downgrade_preserves_rows_without_recovering_secrets(
    database: MigrationDatabase,
) -> None:
    database.migrate("upgrade", "20260901_0002")
    database.query("""
        INSERT INTO business_operations (business_operation_id, operation_type, state)
        VALUES (gen_random_uuid(), 'register', 'completed')
    """)
    before = database.query("SELECT business_operation_id FROM business_operations")
    database.migrate("downgrade", "20260829_0001")
    assert (
        database.query("SELECT business_operation_id FROM business_operations")
        == before
    )
    assert database.query("""
        SELECT octet_length(payload_fingerprint), fingerprint_key_version
        FROM business_operations
    """) == [(32, 1)]
    database.migrate("upgrade", "head")
    assert (
        database.query("SELECT business_operation_id FROM business_operations")
        == before
    )
