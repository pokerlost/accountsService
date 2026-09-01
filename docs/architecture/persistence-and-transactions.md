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
entities, persistence projections, and public API response models remain separate artifacts.

accountsService adds account, password-credential, and resumable-workflow tables and focused
repositories for responsibilities defined in `SERVICE.md`. Public response models remain separate
from those persistence entities and projections.

## Remote calls

There is no current authService call site, so no present request transaction crosses remote I/O.
When an operation adopts a generated authService method, do not hold a PostgreSQL transaction open
across bearer token acquisition, the `pypokerlost` SDK call, or retry backoff. A remote method call
and a local database transaction cannot form one atomic transaction.

Structure a mutation as explicit phases: use a short transaction to establish or load the persisted
business operation and semantic fingerprint, close that transaction, perform the remote call, then
use another short transaction to record the outcome or reconciliation state. Every allowed retry
reuses the same `business_operation_id` and the same semantic payload. Retry is transport recovery,
not a replacement for persisted idempotency or reconciliation after an ambiguous outcome.

Only a verified read-only or contractually idempotent operation receives the explicit per-call
`PokerLostRetryPolicy`; no policy means one attempt. `401`, `403`, idempotency conflicts, validation
failures, and ordinary application failures are not automatically replayed. If a future handler
cannot expose a non-transactional remote-call seam with the existing workflow architecture, that
call remains blocked until the service has an approved safe orchestration boundary.

The prohibited span includes service-owned token acquisition, the first target attempt,
`Retry-After` or jitter backoff sleep, and every later attempt. End the request-owned transaction
before entering that outbound phase. Reuse the service's existing workflow or reconciliation seam
for an ambiguous remote outcome; do not introduce an unowned transaction, hold a session idle, or
treat transport retry as durable business reconciliation.

Mutation retry is allowed only when the target contract persists idempotency and every attempt
uses the same `business_operation_id` and the same semantic payload. The SDK neither creates that
key nor persists fingerprint, workflow, outbox, or reconciliation state. Detailed client and retry
composition is documented in `docs/architecture/inter-service-clients.md`.

## Failure mapping

The engine boundary narrowly converts an exact driver `ConnectionRefusedError` into SQLAlchemy's
`OperationalError`. The centralized API handler maps that availability category to a safe `503`
response. Other `SQLAlchemyError` instances become sanitized `500` responses. The request
dependency does not catch or translate these exceptions.

The exact public forms live in `docs/api/errors.md`. The root probe does not open a session or
establish database readiness; see `docs/api/public-surface.md`.

## Alembic metadata

Alembic owns schema migrations against the shared `Base.metadata`. Every concrete ORM model must be
imported through `persistence.database.models` so migration autogeneration can see it. Do not add a
fake baseline model or migration to an otherwise pristine service. The command workflow and review
discipline are documented in `docs/development/database-migrations.md`.
