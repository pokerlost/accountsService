# Request lifecycle

This page traces composition, server-owned request context, authorization, application execution,
and response handling.

## Composition

`create_app()` resolves settings, configures observability, constructs FastAPI, and registers
request middleware, exception handlers, flat routers, and instrumentation. Lifespan creates the
database engine/session factory and stores them with the optional `PokerlostTokenVerifier` in
`ApplicationResources`. No password service or account model is composed in this foundation.

The current service supplies no verifier because it has no protected route. A real local verifier
is passed only when such a route is implemented. Missing protected composition fails closed.

## Inbound flow

```text
FastAPI
→ server-generated request ID
→ dependencies
→ flat route
→ application handler
→ persistence adapter
→ plain response data
→ FastAPI response_model serialization
```

The request ID is generated server-side and exists only in request state and telemetry. No caller
correlation value is accepted or returned as a transport contract.

Every business route receives `PokerlostRequest[Payload]`. A protected route additionally declares
exact scopes through `Security`. The dependency validates the bearer header, invokes the local
verifier for the exact service-name audience, distinguishes invalid and expired credentials, and
checks every scope before the route executes.

Pydantic request models parse primitive wire values before routes translate them into application
commands or queries. Application handlers return focused results without FastAPI or HTTP response
types. Routes translate those results into plain mappings, and FastAPI validates normal business
successes through `response_model`. Central handlers alone construct the canonical error envelope
and normalize validation, application, database, authentication, authorization and unexpected
failures without exposing submitted input. `/getOpenApi` returns the raw framework document.

## Transactions and outbound calls

A route that declares `DatabaseSession` owns one async transaction. It must end before token
acquisition, refresh, outbound SDK calls, retry sleep, or subsequent attempts. Outbound clients use
retry then authentication middleware as documented in
`docs/architecture/inter-service-clients.md`.

The root and OpenAPI routes stop at the route layer and open no database transaction. The existing
account/password repositories and workflow runtime code have been removed. Historical migration
files remain but are not invoked by either infrastructure route.
