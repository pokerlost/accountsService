# accountsService

Before every task:

1. Read `AGENTS.md` and `SERVICE.md`.
2. Inspect the current repository and relevant implementation.
3. Treat the latest direct user requirement as highest priority.
4. Preserve service-owned behavior, migrations, and local changes.

Priority:

```text
latest direct user requirement
→ SERVICE.md
→ AGENTS.md
→ current implementation
→ older decisions
```

## General architecture

- Keep API, application, domain, configuration, observability, persistence, and CLI
  responsibilities separated.
- Do not introduce an abstraction without a concrete responsibility.
- PostgreSQL remains the primary persistence layer.
- Validate critical settings at startup and fail closed.
- Do not commit or log secrets.

## Pokerlost JSON protocol

- Pokerlost service calls use JSON bodies over HTTPS. Protected operations accept access tokens
  only through the standard `Authorization: Bearer` header.
- `GET /`, `GET /getOpenApi`, and existing health probes are the only public infrastructure
  exceptions. They accept no business body or authentication material.
- Every business/API operation uses `POST /<operationId>` with one JSON request body and one JSON
  `PokerlostResponse` body.
- Every operation ID matches `^[a-z][A-Za-z0-9]*$`. Use a single lowerCamelCase verb name such as
  `getMe`, `registerAccount`, or `provisionHuman`.
- Do not use business path parameters, query parameters, cookies, caller-supplied transport
  metadata, GET bodies, form data, content negotiation, or manual content-type construction.
- Every business operation accepts the same pure `PokerlostRequest[Payload]` JSON envelope. It
  never contains access tokens, headers, request options, method binding, or execution metadata.
- Client credentials belong only in the `getToken` JSON payload. A refresh token belongs only in
  the `refreshToken` JSON payload. Do not prepend a token type string.
- Every static route module owns one module-level `router = APIRouter(...)`; declare its endpoints
  directly at module level with router decorators. Do not use router factories, nested endpoints,
  one-directory-per-router layouts, one-use route constants, imperative registration, or post-hoc
  route mutation.
- Pydantic request models own primitive wire parsing and validation. Route modules do not define
  `_parse_*` or `_validate_*` helpers for UUIDs, enums, audiences, scopes, or other basic input.

## Responses and errors

- Every normal business route declares `pypokerlost.types.PokerlostResponse[ResultT]` as its
  `response_model` and returns plain Python data. FastAPI owns response validation and
  serialization.
- Success requires null error metadata and null `retry_after`. Failure requires a stable error
  code, null result, an optional safe message, and an optional finite non-negative retry delay.
- Do not create a parallel service response envelope or an application-layer Result wrapper with
  the same wire shape.
- Application handlers return focused application result values, never FastAPI responses, HTTP
  status codes, or `PokerlostResponse` models. Routes map those results to plain response data.
- Only centralized exception/error boundary code may construct `PokerlostResponse[None]` manually
  before producing a `JSONResponse`. Normal endpoints do not construct `PokerlostResponse`, call
  `model_dump()`, or return `JSONResponse`.
- Central handlers return sanitized failures and never echo request input, response bodies,
  tracebacks, SQL details, credentials, or tokens.
- Use Pydantic validation, `ValueError`/`TypeError`, application errors, or focused Pokerlost SDK
  errors. Project-owned runtime Python must not use assertions for validation or protocol state.

## Header authorization and scopes

- Pokerlost scopes use dot-separated lowerCamelCase segments and match
  `^[a-z][A-Za-z0-9]*(\.[a-z][A-Za-z0-9]*)+$`. Wildcards and category-based bypasses are forbidden.
- Keep the service-owned catalog in `app/domain/enums/scopes.py` as the sole local `Scopes` enum.
  SDK-owned shared wire enums remain under `pypokerlost/enums/`.
- A protected route declares every exact scope through
  `Security(authorize_pokerlost_request, scopes=[...])`. A public route has no security dependency.
- `PokerlostTokenVerifier` is the transport-independent application port for local verification.
  A concrete service supplies a real verifier at composition only when its implemented stage
  protects a route. The template does not provide a fake verifier or remote verification call.
- The dependency uses FastAPI's standard OAuth2 client-credentials security model with
  `auto_error=False`, parses one bearer header, verifies locally for `SERVICE_NAME`, compares the
  returned audience, and requires every exact route scope.
- Missing/malformed authentication, invalid token, expired token, and insufficient scope use the
  canonical `POKERLOST_*` application errors and central `PokerlostResponse` handler.
- Authorization decisions use exact scopes only. Do not call authService for every protected
  request.
- Protected composition without a configured verifier must fail closed.

## OpenAPI

- Use FastAPI's ordinary OAuth2 security model and OpenAPI generation without manual metadata,
  vendor extensions, route mutation, or post-processing.
- When at least one protected route exists, the local catalog populates the client-credentials
  scheme and protected routes publish their exact non-empty scope lists through
  `Security(..., scopes=[...])`.
- Operations without an access-token requirement publish no security requirement.
- A service with zero protected operations may omit `components.securitySchemes`; never create a
  fake route, empty-scope dependency, injected component, `openapi_extra`, custom `x-*` metadata,
  or handwritten scope map to force one.
- Keep built-in `/openapi.json`, `/docs`, and `/redoc` disabled. Publish the unmodified document
  directly through `GET /getOpenApi`.

## Pokerlost SDK compatibility

- The current `pypokerlost` public facade and generator are authoritative. Use flat public imports
  and do not import private modules, generator internals, or removed compatibility paths.
- Inter-service calls use `PokerlostClient` and generated `PokerlostMethod` classes. Do not add a
  parallel `httpx`, `requests`, or `aiohttp` transport, URL builder, decoder, or remote DTO copy.
- A concrete service creates one target-specific client only for a real dependency declared by
  `SERVICE.md`, owns it in lifespan, stores it in a named `ApplicationResources` field, and closes
  it on shutdown. The pristine service creates no outbound client.
- Protected outbound clients compose middleware in this order:

```text
PokerlostRetryMiddleware
→ PokerlostAuthenticationMiddleware
→ transport
```

- Authentication middleware receives an injected `PokerlostTokenStore` and
  `PokerlostTokenRefresher`; it never owns client credentials or initial token acquisition.
- Public methods have explicit `__scopes__ = None`, bypass token state and send no Authorization
  header. Protected methods have a non-empty exact `__scopes__` tuple. Missing metadata or an empty
  tuple is a local configuration error.
- Retry remains disabled unless a call passes
  `PokerlostRequestOptions(retry_policy=PokerlostRetryPolicy())`. Do not expose retry algorithm
  settings through deployment configuration.
- The retry policy receives server guidance only from `PokerlostResponse.retry_after`. It never
  reads transport metadata.
- Only the exact expired-token error may trigger one reactive refresh and one replay. Invalid-token
  and insufficient-scope failures never trigger refresh.
- Transport retry is not business idempotency. A replayable mutation must reuse the same
  `business_operation_id`, semantic payload, operation, and target. Middleware never creates or
  changes business IDs or workflow persistence.
- Persistent token state uses absolute UTC expiration and version/CAS semantics. Never keep a
  PostgreSQL transaction open during token acquisition, refresh network I/O, an outbound call,
  retry sleep, or another attempt.

## Sensitive data and observability

- Secret-bearing models must use `hide_input_in_errors=True` and repr-hidden fields.
- Never capture or log request/response bodies containing `client_secret`, `access_token`,
  `refresh_token`, passwords, login grants, or private keys.
- Keep FastAPI instrumentation body/header capture disabled and HTTP client debug logging disabled.
- Generate request IDs only on the server. Do not read or return request-correlation transport
  metadata as a public contract.

## Configuration and deployment

- `getRoot` and `getOpenApi` are stable code-defined operation IDs. They are not settings,
  environment variables, Helm values, or deployment policy.
- Put deployment policy in typed settings. Keep protocol invariants and all operation IDs in code.
- Production deployment requires HTTPS/TLS. The generated ClusterIP is an internal target and
  must remain behind trusted TLS termination; do not expose it as a plaintext production API.
- Secrets use environment injection or Kubernetes Secret references, never chart values or
  ConfigMaps.

## Application, domain, and persistence

- Application values and ports remain transport-independent. Ports do not expose FastAPI,
  SQLAlchemy sessions, or concrete SDK clients.
- Reuse `Command`, `Query`, `Result`, and the structural asynchronous `Handler` Protocol.
- Routes translate API schemas to application values; public models do not double as domain or ORM
  models.
- A request-owned SQLAlchemy session owns one transaction. Routes, handlers, repositories, and
  query adapters do not commit or roll back directly.
- Keep repositories focused. When a service needs read projections, keep them separate from ORM
  entities and API responses rather than adding a generic projection framework to the foundation.
- Do not add a fake model or migration to a pristine service.

## Documentation and tooling

- Keep `README.md` as the landing page and `docs/index.md` as the documentation home.
- Write documentation in English with one H1, repository-root file references, language-tagged
  fences, and no relative inter-file links.
- Update `docs/api/public-surface.md` for every implemented operation. Wire changes also update the
  response, header authorization, operation, and OpenAPI pages.
- Use the repository `Makefile`, `uv`, Ruff, mypy, Alembic, Docker, and Helm conventions.
- Do not add or modify tests unless the direct user task explicitly requests tests. Do not add
  rendered-template tests or make ordinary quality targets depend on an unrequested test suite.
- Do not add `scripts/check_*.py`, rendered-template alignment checkers, renamed equivalents, or
  hidden checker logic in Make/pre-commit. Use disposable direct commands for one-time inspection.
- Before handoff, run `make format`, `make check`, `make pre-commit`, and report every unavailable
  or failed check.
