# Project status

`accountsService` is a local foundation derived from the current Pokerlost `serviceTemplate`. Product account behavior is deferred.

## 🧭 Available now

FastAPI composition, typed settings, safe errors, standard logging, PostgreSQL engine and request transaction, Alembic, Docker, Helm, and existing quality tooling remain. `GET /`, `GET /getOpenApi`, `/health/live`, and `/health/ready` are the only routes. Readiness checks the required database and returns 503 when unavailable. The scope catalog is empty, no protected route uses the optional verifier port, and no outbound authService client is composed.

## 📦 Deferred

Account and password models, concrete repositories, Argon2 policy, resumable workflows, product handlers/routes, authService coordination, and deployment credentials are not implemented in the current runtime. Their intended ownership is in [SERVICE.md](../../SERVICE.md); SDK methods do not imply server implementation. Add a future stage only with a reviewed contract, migration, failure behavior and tests when separately permitted.

## 🗄️ Historical data boundary

Three historical Alembic revision files moved unchanged into `migrations/versions/`; they may create legacy account tables on a fresh database. Runtime metadata is empty. No production database was accessed, no destructive migration was made, and autogenerate is not a safe deletion plan. The prior local commit and private backup retain the old flat runtime.

See [public surface](../api/public-surface.md) and [persistence](../architecture/persistence-and-transactions.md) for exact current boundaries.
