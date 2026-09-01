# Architecture overview

This page defines the generated service layers and their dependency direction without prescribing
business behavior that belongs to a concrete service.

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
and translates results into API responses. `application` owns transport-independent use-case
orchestration and builds its typed command, query, and result values on the framework-independent
`domain` foundation.

Composition code supplies concrete persistence adapters where an operation needs them. Application
behavior does not import FastAPI, and domain values do not depend on transport, settings,
observability, or SQLAlchemy. Configuration and observability support the runtime as infrastructure
concerns; they do not own service use cases.

## Layer responsibilities

| Layer | Responsibility |
| --- | --- |
| `api` | Application factory, lifespan, middleware, dependencies, routes, public schemas, OpenAPI, and safe errors. |
| `application` | Commands, queries, results, meaningful Protocol ports, handler contracts, and concrete use-case orchestration. |
| `domain` | Framework-independent internal values and closed domain or platform categories. |
| `persistence` | SQLAlchemy metadata, sessions, repositories, result readers, projections, and concrete adapters. |
| `configuration` | Typed settings, environment loading, and startup validation. |
| `observability` | Privacy-safe Logfire configuration and FastAPI/SQLAlchemy instrumentation. |
| `cli` | Operator entry points such as local application startup. |

Public request and response models remain API artifacts; ORM models and projections remain
persistence artifacts. A route performs the explicit translation between those boundaries rather
than sharing one model across layers.

## Outbound integration boundary

No current route or application handler calls authService, so the composition root has no outbound
client, token port or adapter, credentials, scopes, token storage, or retry policy. Existing
persisted provisioning and synchronization state is a local workflow foundation, not proof that a
remote call is implemented.

When an actual generated authService method is adopted, `api` composition owns one target-specific
lifespan client and publishes it through an explicitly named typed `ApplicationResources` field.
Application orchestration consumes a service-owned port implemented by a focused pypokerlost
adapter. That adapter calls the generated `oauth.token` method when its use case requires a token
and supplies authentication through generic per-call headers. The SDK does not own credentials,
token storage, refresh, or bearer middleware. Retry remains disabled unless a replay-safe call opts
in with `RequestOptions(retry=PokerLostRetryPolicy())`; no database transaction spans a remote
attempt or retry sleep.

## Runtime foundation

`docs/architecture/request-lifecycle.md` explains composition and per-request flow.
`docs/architecture/persistence-and-transactions.md` defines PostgreSQL session ownership. The API
wire surface is documented separately in `docs/api/overview.md`. When `SERVICE.md` declares a real
outbound target, `docs/architecture/inter-service-clients.md` defines the target-specific SDK
client, service-owned token port and adapter, retry, dependency, and lifecycle extension.

`SERVICE.md` defines the accounts domain responsibilities implemented by the existing entities,
repositories, migration, and security/idempotency primitives. A concrete HTTP operation is added
only with its complete application orchestration and authorization contract.
