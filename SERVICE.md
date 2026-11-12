# accountsService

`accountsService` is the proposed owner of human accounts and password credentials in Pokerlost. The present checkout is a **service foundation**, not an implemented account API.

## 🧭 Foundation available

The committed `serviceTemplate` provides FastAPI composition, typed configuration, safe Pokerlost errors, optional bearer-verifier port, PostgreSQL engine/session ownership, Alembic, logging, Docker, and Helm. `GET /`, `GET /getOpenApi`, `/health/live`, and `/health/ready` are the only routes. No account/password entities, concrete repositories, handlers, scopes, outbound authService client, or product endpoint are registered. The database setting is required by this specialized template, but no connection is opened on module import.

Runtime source lives in `src/accountsservice/`. Rules, the empty exact scope catalog, and the three historical revisions in `migrations/versions/` are project-owned. Historical revisions remain unchanged; moving source files does not apply a database migration or establish release status.

Existing Alembic revisions are historical artifacts from an earlier account implementation. They remain immutable and may still create old tables when run on a fresh database; the current ORM metadata does not claim those tables. Do not run autogenerate, upgrade or destructive cleanup against production without a separately reviewed migration plan.

## 📦 Planned ownership

A later business stage may own account IDs, canonical usernames, mutable nicknames, password hashes, account lifecycle, staff creation and resumable account workflows. Its exact API, schema, migrations, idempotency semantics and authorization requirements need separate design and review. SDK stubs are not evidence of current server operations.

`authService` owns authorization principals, exact scope grants, sessions and tokens. `accountsService` must not issue tokens, store authService passwords, read its database, or hold a PostgreSQL transaction across SDK network I/O. Pokerlost inter-service calls use the pinned `pypokerlost` transport with a concrete target and credential lifecycle only when a real operation needs them. No allow-all verifier or direct HTTP fallback is installed.

## 🔒 Deferred security rules

These are requirements for a future password implementation, **not current configuration or code**:

- Password input is preserved exactly, without trimming or normalization; plaintext never reaches logs or storage.
- Username is canonical; nickname is mutable, Unicode and non-unique, with 1–64 characters after surrounding whitespace is stripped.
- The prior candidate password length was 12–256 characters. Argon2id baseline was 65536 KiB memory, time cost 3, parallelism 4, hash length 32 and salt length 16. Revalidate this policy when implementing; no Argon2 dependency is installed now.
- Unknown accounts need a safe verification path, and reused business-operation IDs must compare semantic payloads before any remote retry.

See [public surface](docs/api/public-surface.md) and [project status](docs/project/status.md) for the current implementation. Restoring earlier source code is not a database rollback plan.
