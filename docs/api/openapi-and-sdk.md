# OpenAPI and SDK

`accountsService` publishes the unmodified FastAPI OpenAPI 3.1 document directly through
`GET /getOpenApi`.

## Publication

The path `/getOpenApi` and operation ID `getOpenApi` are stable code-defined contracts rather than
deployment settings. Built-in `/openapi.json`, `/docs`, and `/redoc` routes are disabled.

The document contains ordinary paths, request schemas, response schemas, summaries, descriptions,
tags and status responses. It contains no project extension, service identity, custom Python
metadata or document post-processing.

Protected operations use FastAPI's standard OAuth2 client-credentials security model. The scheme
publishes the local scope catalog and each protected route publishes its exact non-empty
requirement. Operations without access-token scopes have no security requirement. The current
service exposes no protected route, so its actual document does not contain an unused security
component. A missing `components.securitySchemes` section is therefore valid when the document has
zero protected operations.

## Generation

The authoritative generator reads all available service documents together, skips infrastructure
routes, validates the POST/JSON/envelope/security contract and global name uniqueness, then writes
flat method and type modules. `PokerlostScopes` is the explicit SDK-owned shared catalog. For a
protected operation, the generator extracts a non-empty scope tuple from standard OAuth2 security
requirements and verifies every value against that catalog. For a public operation, including a
document with no security scheme, it emits `__scopes__ = None`; missing or empty protected method
metadata is invalid.

Manual future-facing method stubs remain outside the generator manifest unless explicitly owned.
They perform ordinary SDK calls when their endpoints exist and never return synthetic success.

## Calls

Inter-service calls use `PokerlostClient` and generated `PokerlostMethod` classes. Every call
serializes `PokerlostRequest`; protected calls obtain an internal typed access token and only the
transport emits the bearer header. The complete lifecycle is in
`docs/architecture/inter-service-clients.md`.
