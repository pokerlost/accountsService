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
- `GET /getOpenApi` publishes the raw FastAPI OpenAPI document.

Their operation IDs are `getRoot` and `getOpenApi`; the root HTTP path is always `/`.

Their exact contract is listed in `docs/api/public-surface.md`.

## Intentionally absent

Concrete HTTP account operations, remote-service clients, and a concrete token verifier are absent
until their complete application flows are implemented. Existing account entities, repositories,
and resumable workflow state are service-owned foundations rather than published API operations.
The capability catalog, verifier port and fail-closed bearer dependency are reusable foundation
rather than an active protected HTTP surface.

The SDK transport/middleware boundary and explicit `PokerlostRetryPolicy` opt-in are documented in
`docs/architecture/inter-service-clients.md`. These are extension points, not default runtime
resources: this service has no target URL, client identity, client secret, shared token state,
refresher or unused client because it has no current authService call site. Planned provisioning and
synchronization state stores explicit scope sets, but the future handler must still compare those
semantic fields when an existing business operation ID is reused.

`SERVICE.md` must define the concrete service purpose, responsibilities, and service-specific rules
before those capabilities are added. Future domain documentation should describe only
responsibilities established there and must be listed in `docs/index.md` when introduced.

See `docs/architecture/overview.md` for layer ownership and
`docs/development/contributing.md` for change discipline.
