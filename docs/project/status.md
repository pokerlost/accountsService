# Project status

This page records the intentional current state of `accountsService`.

## Ready foundation

The repository provides the FastAPI composition root, typed configuration, a server-generated
request ID, canonical response errors, Logfire instrumentation, mandatory PostgreSQL transaction
ownership, Alembic, Docker, Helm, and the locked quality workflow. It also contains the
account/password domain, resumable-workflow persistence, and one lifespan-owned configured
password service.

The two base endpoints are ready with the `.env.example` values:

- `GET /` returns the service root envelope;
- `GET /getOpenApi` publishes the wrapped FastAPI OpenAPI document.

Their operation IDs are `getRoot` and `getOpenApi`; the root HTTP path is always `/`.

Their exact contract is listed in `docs/api/public-surface.md`.

## Intentionally absent

Concrete HTTP account operations, remote-service clients, and a concrete token verifier are absent
until their complete application flows are implemented. Existing account entities, repositories,
and resumable workflow state are service-owned foundations rather than published API operations.
The empty scope catalog, verifier port, and fail-closed body dependency are reusable foundation
rather than active authorization policy.

The SDK transport/middleware boundary and explicit `PokerlostRetryPolicy` opt-in are documented in
`docs/architecture/inter-service-clients.md`. These are extension points, not default runtime
resources: this service has no target URL, client ID, client secret, scope bundle, token cache, or
unused client because it has no current authService call site.

`SERVICE.md` must define the concrete service purpose, responsibilities, and service-specific rules
before those capabilities are added. Future domain documentation should describe only
responsibilities established there and must be listed in `docs/index.md` when introduced.

See `docs/architecture/overview.md` for layer ownership and
`docs/development/contributing.md` for change discipline.
