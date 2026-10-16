# Project status

`accountsService` is a local foundation derived from the current Pokerlost `serviceTemplate`. Product account behavior is deferred.

## 🧭 Available now

FastAPI composition, typed settings, safe errors, Logfire instrumentation, PostgreSQL engine and request-transaction mechanism, Alembic, Docker, Helm, and existing quality tooling remain. `GET /` and `GET /getOpenApi` are the only routes. They prove process response, not database readiness. The scope catalog is empty, no protected route uses the optional verifier port, and no outbound authService client is composed.

## 📦 Deferred

Account and password models, concrete repositories, Argon2 policy, resumable workflows, product handlers/routes, authService coordination, and deployment credentials are not implemented in the current runtime. Their intended ownership is in [SERVICE.md](../../SERVICE.md); SDK methods do not imply server implementation. Add a future stage only with a reviewed contract, migration, failure behavior and tests when separately permitted.

## 🗄️ Historical data boundary

Earlier Alembic revisions remain unchanged and may create legacy account tables on a fresh database. Runtime metadata is now empty. No production database was accessed, no destructive migration was made, and `alembic check`/autogenerate must not be interpreted as a safe deletion plan. The private backup captures the removed local source.

See [public surface](../api/public-surface.md) and [persistence](../architecture/persistence-and-transactions.md) for exact current boundaries.
