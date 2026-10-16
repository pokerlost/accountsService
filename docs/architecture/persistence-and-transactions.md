# Persistence and transactions

This page is the canonical ownership contract for PostgreSQL, SQLAlchemy sessions, repositories,
and Alembic in the generated service.

## PostgreSQL ownership

PostgreSQL is the unconditional source of truth for persisted service state. The process owns one
async engine and session factory in application lifespan. A database-consuming request owns one
`AsyncSession`; sessions are not shared between requests.

The database dependency uses SQLAlchemy's transaction context directly:

```python
async with resources.session_factory.begin() as session:
    yield session
```

Normal context exit commits, exceptional exit rolls back, and context completion closes the
session. Routes, application handlers, repositories, and query adapters do not call `begin()`,
`commit()`, or `rollback()`.

## Persistence adapters

Repositories and query adapters receive the request session and execute explicit SQLAlchemy 2
statements. They do not create engines or sessions and do not complete the transaction. ORM
entities and public API response models remain separate artifacts. A service that needs a read
projection defines that focused type in its persistence layer and translates it explicitly.

The template supplies metadata and a narrow repository execution base without generic
result-reader or projection wrappers. `accountsService` currently adds no concrete ORM model or
repository. Its earlier account/password migration revisions are historical artifacts, not a
declaration that those tables are active runtime state.

## Remote calls

There is no current authService call site, so no present request transaction crosses remote I/O.
When an operation adopts a generated authService method, do not hold a PostgreSQL transaction open
across token acquisition, the SDK call, or retry backoff. A remote method call and a local database
transaction cannot form one atomic transaction. Structure the workflow as explicit short local
phases around the remote call without treating either side as a distributed commit participant.

The prohibited span includes service-owned token acquisition, the first target attempt,
server-directed or jitter backoff sleep, and every later attempt. End the request-owned transaction
before entering that outbound phase. Reuse the service's existing workflow or reconciliation seam
for an ambiguous remote outcome; do not introduce an unowned transaction, hold a session idle, or
treat transport retry as durable business reconciliation.

Mutation retry is allowed only when the target contract persists idempotency and every attempt
uses the same `business_operation_id` and the same semantic payload. The SDK neither creates that
key nor persists workflow, outbox, or reconciliation state. Detailed client and retry
composition is documented in `docs/architecture/inter-service-clients.md`.

The prior business-operation repository has been removed from the current foundation. A future
workflow must prove semantic payload equivalence before replaying a reused operation ID; neither
the SDK retry policy nor a historical table provides that guarantee.

## Failure mapping

The engine boundary narrowly converts an exact driver `ConnectionRefusedError` into SQLAlchemy's
`OperationalError`. The centralized API handler maps that availability category to a safe `503`
response. Other `SQLAlchemyError` instances become sanitized `500` responses. The request
dependency does not catch or translate these exceptions.

The exact public forms live in `docs/api/errors.md`. The root probe does not open a session or
establish database readiness; see `docs/api/public-surface.md`.

## Alembic metadata

Alembic owns schema migrations against the shared `Base.metadata`. Every concrete ORM model must be
imported through `persistence.database.models` so migration autogeneration can see it. The current
model registry is empty; historical revisions may create legacy tables when upgrading a fresh
database. Do not autogenerate a drop migration from the empty metadata or run an upgrade against
production during foundation cleanup. Add a future model and forward migration only for a
reviewed responsibility in `SERVICE.md`; never rewrite an applied revision.
The command workflow and review discipline are documented in
`docs/development/database-migrations.md`.
