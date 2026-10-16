# Architecture overview

This page defines the service layers and their dependency direction.

## Dependency direction

The core request dependency direction is:

```text
api
-> application
-> domain

api/application composition
-> persistence adapters

api/application composition
-> target-specific pypokerlost clients

application
-> meaningful service-owned ports

target-specific adapters
-> generated pypokerlost methods

configuration and observability
-> infrastructure concerns
```

`api` owns FastAPI transport and composition. It translates public schemas into application values
and translates application results into plain response data for FastAPI's declared response
models. `application` owns transport-independent use-case orchestration and builds its typed
command, query, and result values on the framework-independent `domain` foundation.

Composition code supplies concrete persistence adapters where an operation needs them. Application
behavior does not import FastAPI, and domain values do not depend on transport, settings,
observability, or SQLAlchemy. Configuration and observability provide runtime infrastructure; they
do not own service use cases.

## Layer responsibilities

| Layer | Responsibility |
| --- | --- |
| `api` | Application factory, lifespan, middleware, dependencies, routes, public schemas, OpenAPI, and safe errors. |
| `application` | Commands, queries, results, meaningful Protocol ports, handler contracts, and concrete use-case orchestration. |
| `domain` | Framework-independent internal values and closed domain or platform categories. |
| `persistence` | SQLAlchemy metadata, sessions, repository execution, and concrete adapters. |
| `configuration` | Typed settings, environment loading, and startup validation. |
| `observability` | Privacy-safe Logfire configuration and FastAPI/SQLAlchemy instrumentation. |
| `cli` | Operator entry points such as local application startup. |

Public request and response models remain API artifacts; ORM models remain persistence artifacts.
When a service needs a read projection, it is a focused persistence artifact. A route performs the
explicit translation between those boundaries rather than sharing one model across layers.
Service-owned enums, including `Scopes`, live under `app/domain/enums/`; SDK-owned shared wire
enums remain under `pypokerlost/enums/` and are mapped at an adapter boundary when necessary.

## Runtime foundation

`docs/architecture/request-lifecycle.md` explains composition and per-request flow.
`docs/architecture/persistence-and-transactions.md` defines PostgreSQL session ownership. The API
wire surface is documented separately in `docs/api/overview.md`. When `SERVICE.md` declares a real
outbound target, `docs/architecture/inter-service-clients.md` defines the target-specific SDK
client, middleware, token-store ownership, retry, and lifecycle extension. Inbound local
verification uses the application port described in `docs/api/header-authorization.md`.

The current runtime owns no account/password domain values, Argon2id service, concrete account
models or repositories. Historical migrations remain in the tree but are not runtime metadata.
There is no authService call site, so composition has no outbound client, target settings,
credentials, token storage or applied retry policy. Add these resources only with a reviewed
business flow and its data/compatibility contract.
