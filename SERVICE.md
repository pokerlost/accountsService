# accountsService

SERVICE_NAME: accountsService
SERVICE_SLUG: accountsservice

## Purpose

Own human accounts, canonical usernames, nicknames, password credentials
and human login confirmation for Pokerlost.

accountsService is a game-agnostic platform service. It does not own games,
events, tournaments, bets, balances or blockchain business logic.

## Responsibilities

- Own human account identifiers and account lifecycle.
- Own canonical usernames and mutable display nicknames.
- Own public registration and staff-account creation.
- Own Argon2id password hashes and password verification.
- Perform dummy password verification for unknown accounts.
- Confirm human credentials and request one-time login grants from authService.
- Orchestrate human principal provisioning in authService.
- Orchestrate principal status and exact-scope synchronization.
- Maintain the account_id to auth_principal_id binding.
- Provide self-service, staff provisioning and account-lifecycle operations.
- Maintain resumable and idempotent distributed account workflows.

## Service-specific rules

- Public means that an operation has no access-token scope requirement.
- Protected operations authorize only through exact Pokerlost capability scopes.
- Human and service identity are distinguished by `PrincipalType`, not by access categories.
- authService is authoritative for direct principal/client scope grants, sessions and tokens.
- accountsService is authoritative for usernames, nicknames and password credentials.
- Access and refresh tokens are issued only by authService.
- Passwords and password hashes never enter authService.
- JWT access tokens are validated locally using authService public keys.
- Pokerlost inter-service calls use generated pypokerlost methods.
- Direct HTTP clients and direct access to another service database are forbidden.
- PostgreSQL transactions must never span SDK network calls.
- Passwords, password hashes, tokens and login grants must not enter logs.

### Outbound authService integration

The current HTTP surface has no implemented operation that calls authService, and accountsService
does not import or call a generated authService business method. It therefore has no authService
client, target settings, client credentials, requested scope bundle, or Kubernetes secret wiring.

When a concrete operation introduces that dependency:

- create one target-specific `PokerlostClient` in FastAPI lifespan, store it in an explicitly typed
  `ApplicationResources` field, reuse it across requests, and close it on shutdown;
- configure `PokerlostAuthenticationMiddleware` only with an injected shared
  `PokerlostTokenStore`, `PokerlostTokenRefresher`, client identity and exact target audience;
- let each generated method supply its exact `__scopes__`; never request a wildcard or a
  service-wide scope bundle;
- acquire the initial token explicitly through generated `GetToken` orchestration, then persist the
  encrypted token state before protected calls begin;
- let the SDK transport alone translate its typed internal token field into
  `Authorization: Bearer`; service code never constructs headers;
- allow one reactive refresh and one replay only for the exact canonical expired-token error;
- coordinate rotating refresh tokens across replicas with persistent version/CAS state and a
  bounded lease that does not hold a PostgreSQL transaction during network I/O;
- keep retry disabled unless a semantically safe call passes
  `PokerlostRequestOptions(retry_policy=PokerlostRetryPolicy())`;
- retry a mutation only with the same `business_operation_id` and the same semantic payload, backed
  by the target operation's persisted idempotency contract;
- never refresh on invalid-token or insufficient-scope failures, and never hold a request-owned
  PostgreSQL transaction across token acquisition, refresh, the remote call, or retry backoff;
- keep client credentials, access tokens, refresh tokens, and sensitive payloads out of source,
  ConfigMaps, errors, representations, telemetry, and logs; OpenAPI publishes the standard security
  contract but never concrete secret values.

No approved reversible token-encryption adapter currently exists in this repository. Its concrete
implementation is therefore a blocker for the first outbound protected workflow, not a reason to
add plaintext storage or a process-local substitute now.

### Capability scopes

The service-owned catalog contains:

```text
accounts.self.getMe
accounts.self.updateNickname
accounts.account.read
accounts.staff.create
accounts.account.disable
accounts.account.enable
accounts.account.replaceScopes
```

No current HTTP operation consumes these capabilities because no account business route is
implemented yet.

### Business-operation reuse

`BusinessOperationRepository.register_or_load()` currently proves only that a reused
`business_operation_id` has the same operation type. Provisioning and synchronization tables keep
their semantic account/status/scope fields, but no current application handler compares those
fields on reuse. The first implementing business stage must perform that comparison before replay;
the generic repository and transport retry do not claim semantic payload equivalence.

### Nickname policy

- Nicknames are Unicode, mutable and non-unique.
- Strip surrounding whitespace before validation and storage.
- The stored nickname must contain 1 to 64 characters after stripping.

### Password input policy

- Treat the exact user input as the password; never strip, lowercase or Unicode-normalize it.
- The default accepted length is 12 to 256 characters, with no composition rules.
- Load the validated minimum and maximum from `password` settings; do not hardcode them in request
  handling or hashing code.
- Never persist or log plaintext passwords.

### Argon2id baseline

```text
type = Argon2id
memory_cost = 65536 KiB
time_cost = 3
parallelism = 4
hash_len = 32
salt_len = 16
```

These baseline values are typed deployment settings. Changes are applied by constructing one
process-owned password service at startup; stored Argon2id hashes are rehashed only after a
successful verification when the active policy differs.
