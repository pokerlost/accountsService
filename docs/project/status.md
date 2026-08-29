# Project status

This page records the intentional current state of `accountsService`.

## Ready foundation

The repository provides the FastAPI composition root, typed configuration, request context, safe
error mapping, Logfire instrumentation, mandatory PostgreSQL session and transaction ownership,
Alembic integration, Docker packaging, Helm resources, and the locked local quality workflow. It
also contains the account/password domain, persistence models for resumable distributed account
workflows, deterministic keyed fingerprints, and one lifespan-owned configured password service.

The two base endpoints are ready with the `.env.example` values:

- `GET /` returns the service root envelope;
- `GET /openapi.get` publishes the wrapped FastAPI OpenAPI document.

Their operation IDs and the OpenAPI publication path are settings-driven; the root HTTP path is
always `/`.

Their exact contract is listed in `docs/api/public-surface.md`.

## Intentionally absent

Concrete HTTP account operations, remote-service clients, authentication, and authorization are
not exposed until their complete application flows are implemented. Existing account entities,
repositories, migration, and idempotency state are service-owned foundations rather than published
API operations.

`SERVICE.md` must define the concrete service purpose, responsibilities, and service-specific rules
before those capabilities are added. Future domain documentation should describe only
responsibilities established there and must be listed in `docs/index.md` when introduced.

See `docs/architecture/overview.md` for layer ownership and
`docs/development/contributing.md` for change discipline.
