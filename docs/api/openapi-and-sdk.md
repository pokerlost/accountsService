# OpenAPI and SDK

This page defines how `accountsService` publishes its FastAPI contract and how that contract is
consumed by the authoritative `pypokerlost` tooling.

## Publication endpoint

`Settings.openapi_operation` supplies both the publication `operation_id` and its
`"/" + operation_id` path. The generated `.env.example` uses `openapi.get`, so its default example
path is `GET /openapi.get`. The operation accepts no parameters or request body and returns the
OpenAPI JSON object as the `result` of `OpenAPIResponse`. `OpenAPIResponse` is an
`ApplicationResponse` specialization, so publication uses the same success and failure invariants
as every other operation.

FastAPI's built-in `/openapi.json`, `/docs`, and `/redoc` routes are disabled. The application calls
FastAPI's `get_openapi()` for its registered routes, caches the resulting OpenAPI 3.1 document, and
adds exactly this required platform extension:

```yaml
x-pokerlost-service:
  id: accountsService
```

The identifier is the canonical Copier service identity, while API operation namespaces follow the
separate rules in `docs/api/operation-contract.md`. `info.version` comes from the
`application.version` setting and remains a semantic version.

Concrete security declarations come from the concrete service's FastAPI dependencies. The wrapper
preserves FastAPI-generated security metadata without constructing or rewriting it.

## Method generation

The authoritative generator reads the wrapped publication, ignores the two system paths, and
creates typed `PokerlostMethod` and response classes for compatible service operations. The
pristine service has no business operation, so it intentionally produces no callable service
method.

Generation is repository-owned development tooling in the authoritative `pypokerlost` checkout;
it is not an installed command in the runtime SDK distribution. Service mode receives the
publication operation explicitly through `--openapi-operation`; its default remains `openapi.get`.
When the wire contract changes, run the compatibility workflow against the current SDK source and
verify both service-mode and saved-file generation. The exact operation, request, response, and
supported-schema requirements are documented in `docs/api/operation-contract.md` and
`docs/api/application-response.md`.

## Inter-service calls

PokerLost services call one another only through `pypokerlost.Client` and generated methods and
response types. A concrete service creates a client only for a target declared by its
`SERVICE.md`, owns that client in application lifespan, reuses it across requests, and closes it on
shutdown. It does not create a parallel HTTP client, URL builder, response decoder, or local copy
of a remote service DTO.

accountsService currently imports and calls no generated authService business method. Its runtime
therefore has no authService client, target settings, client credentials, requested OAuth2 scopes,
or deployment secret. The authService responsibilities in `SERVICE.md` do not by themselves justify
an unused client.

When an implemented operation creates a real authService dependency, composition uses these public
facades:

```python
from pypokerlost import Client
from pypokerlost.client.api_server import APIServer
from pypokerlost.client.auth import ClientCredentials, ClientCredentialsTokenProvider
from pypokerlost.client.request import RequestOptions
from pypokerlost.client.retry import RetryPolicy
from pypokerlost.client.session import HttpxSession
from pypokerlost.middleware import BearerTokenMiddleware, RetryMiddleware
```

The lifespan creates one provider and one target-specific `Client`, using an `HttpxSession` for the
validated target `APIServer`. The client middleware tuple is ordered as
`(RetryMiddleware(), BearerTokenMiddleware(provider))`: the first component is outermost, so each
explicit retry attempt re-enters bearer resolution while the provider normally serves a valid token
from its process-local cache. The client is started before its typed `ApplicationResources` field is
published and closed before resources on which it depends.

`ClientCredentialsTokenProvider` sends the focused form-and-HTTP-Basic `/oauth.token` request inside
the SDK and decodes both success and failure through the universal `ApplicationResponse` contract.
The consuming service does not construct that request, cache raw tokens, inject `Authorization`
itself, or add a direct `httpx`, `requests`, or `aiohttp` fallback. Neither the provider nor bearer
middleware performs automatic `401` or `403` replay.

The target resource is fixed in code as `urn:pokerlost:service:authService`. The immutable scope
bundle contains only exact scopes required by generated operations that accountsService actually
calls. Because the current call set is empty, the current scope bundle is also empty and no provider
is constructed; wildcard and future scopes are not requested.

Installing `RetryMiddleware` does not enable retry. A verified read-only or contractually
idempotent call opts in with `RequestOptions(retry=RetryPolicy(...))`; an ordinary call omits that
option and makes one attempt. A mutation replay must keep the same `business_operation_id` and the
same semantic payload. accountsService persists that business identity, fingerprint, workflow, and
reconciliation state; the SDK does not. A PostgreSQL transaction must not span token acquisition,
the target call, or backoff sleep. See `docs/architecture/persistence-and-transactions.md` for that
boundary.

The current pristine endpoints and their publication models are listed in
`docs/api/public-surface.md`.
