# Inter-service clients

This page defines the opt-in extension boundary for a future concrete outbound Pokerlost
dependency.

The current HTTP surface calls no other service. It therefore creates no client, credentials,
token persistence, refresher or retry configuration.

## Ownership

The SDK owns typed methods/types, `PokerlostClient`, transport, response decoding, canonical
errors, retry middleware, bearer injection and the narrow reactive refresh trigger. The consuming
service owns target configuration, client credentials, initial `GetToken` orchestration, persistent
encrypted token state, refresh coordination and business replay policy.

When an implemented use case needs authService, create one target-specific `PokerlostClient` in
lifespan, expose it through one named `ApplicationResources` field, reuse it and close it on
shutdown. Do not create direct HTTP transport, a string-keyed client registry or per-request
clients.

## Authentication boundary

A protected client composes:

```text
PokerlostRetryMiddleware
→ PokerlostAuthenticationMiddleware
→ transport
```

`PokerlostAuthenticationMiddleware` receives only an injected `PokerlostTokenStore`, an injected
`PokerlostTokenRefresher`, client identity and target audience. It does not receive or persist
client credentials and never calls `GetToken` when state is missing.

Initial acquisition is explicit service orchestration:

```text
service-owned credentials
→ generated GetToken call
→ validate PokerlostResponse
→ persist shared encrypted token state
→ enable protected target calls
```

For `method.__scopes__ is None`, middleware bypasses token storage and sends no Authorization
header. A non-empty tuple loads state by client identity, exact service-name audience and canonical
scope set. Missing metadata, an empty tuple or missing state fails locally before target I/O. Only
the transport renders `Authorization: Bearer <access-token>`; every JSON body remains a pure
`PokerlostRequest`.

## Reactive refresh

Timezone-aware UTC `expires_at` remains persistent coordination metadata and does not trigger a
refresh before the first target attempt. Only a target response with
`POKERLOST_ACCESS_TOKEN_EXPIRED` invokes the injected refresher at most once, rebuilds authorization
state and replays the identical operation, body and `business_operation_id` exactly once.
Invalid-token and insufficient-scope failures do not refresh.

Production state is shared between replicas and versioned for compare-and-swap. A refresher for a
rotating refresh token uses a bounded cross-process lease, performs network I/O outside a database
transaction and lets stale workers reload a newer stored version. Persisted expiration never uses
a process-local monotonic clock.

No approved reversible token-encryption adapter currently exists in this repository. The first
outbound protected workflow must provide one before composition; plaintext token storage and a
process-local substitute are not acceptable interim implementations.

## Retry and business safety

Retry is explicit per logical call:

```python
from pypokerlost import PokerlostRequestOptions
from pypokerlost.middleware import PokerlostRetryPolicy

options = PokerlostRequestOptions(
    retry_policy=PokerlostRetryPolicy(),
)
```

The immutable policy uses at most three attempts including the first, full jitter and a
five-second logical budget. It retries canonical connection/timeout failures and statuses `408`,
`425`, `429`, `500`, `502`, `503` and `504`. Server delay comes only from body `retry_after`.
Cancellation propagates immediately.

Transport retry is not business idempotency. Every replay-safe mutation needs the same
`business_operation_id`, semantic payload, operation and target. The current generic business
operation repository compares only operation type on key reuse; a later implementing handler must
also compare its persisted subtype fields before replay. Middleware never creates business IDs or
owns workflow persistence.

Never keep a PostgreSQL transaction open during acquisition, refresh, a target attempt or retry
backoff. Secrets and raw request/response bodies do not enter representations, errors or telemetry.
