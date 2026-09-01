# accountsService

SERVICE_NAME: accountsService
SERVICE_SLUG: accountsservice

## Purpose

Own human accounts, canonical usernames, nicknames, password credentials
and human login confirmation for PokerLost.

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
- Orchestrate principal status and role synchronization.
- Maintain the account_id to auth_principal_id binding.
- Provide self-service, support-safe and master account-management operations.
- Maintain resumable and idempotent distributed account workflows.

## Service-specific rules

- Canonical access categories are public, user, support, master and auto.
- Public means unauthenticated access and is not a persisted role.
- Human accounts may have only user, support or master roles.
- Auto is reserved for service principals and never has a HumanAccount or password.
- Roles have no implicit inheritance.
- Master is not a global authorization bypass.
- Protected operations authorize through OAuth2 scopes, never through role checks.
- authService is authoritative for roles, scope grants, sessions and tokens.
- accountsService is authoritative for usernames, nicknames and password credentials.
- Access and refresh tokens are issued only by authService.
- Passwords and password hashes never enter authService.
- JWT access tokens are validated locally using authService public keys.
- PokerLost inter-service calls use generated pypokerlost methods.
- Direct HTTP clients and direct access to another service database are forbidden.
- PostgreSQL transactions must never span SDK network calls.
- Passwords, password hashes, tokens and login grants must not enter logs.

### Outbound authService integration

The current HTTP surface has no implemented operation that calls authService, and accountsService
does not import or call a generated authService business method. It therefore has no authService
client, target settings, client credentials, requested scope bundle, or Kubernetes secret wiring.

When a concrete operation introduces that dependency:

- create one target-specific `pypokerlost.Client` in FastAPI lifespan, store it in an explicitly
  typed `ApplicationResources` field, reuse it across requests, and close it on shutdown;
- define a service-owned application port for token acquisition and implement it with a
  service-owned pypokerlost adapter that calls the generated `oauth.token` method;
- keep client credentials, requested scopes, target resource, and any token storage or refresh
  orchestration in accountsService composition rather than the SDK;
- use the exact target resource `urn:pokerlost:service:authService` and request only scopes required
  by generated operations that are actually called;
- keep retry disabled unless a semantically safe call passes
  `RequestOptions(retry=PokerLostRetryPolicy())`;
- retry a mutation only with the same `business_operation_id` and the same semantic payload, backed
  by the target operation's persisted idempotency contract;
- never replay `401` or `403` automatically, and never hold a request-owned PostgreSQL transaction
  across token acquisition, the remote call, or retry backoff;
- keep client credentials, authorization headers, access tokens, and sensitive payloads out of
  source, ConfigMaps, OpenAPI, errors, representations, telemetry, and logs.

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

### Business-operation fingerprints

- Persist only the HMAC-SHA-256 digest and its positive key version, never canonical plaintext.
- Build fingerprints from explicit semantic fields for each concrete idempotent operation.
- Supply the fingerprint secret through
  `ACCOUNTSSERVICE_BUSINESS_OPERATION_FINGERPRINT__SECRET` and keep it out of ConfigMaps, logs,
  OpenAPI, and committed configuration.
- Configure the non-secret active version through
  `ACCOUNTSSERVICE_BUSINESS_OPERATION_FINGERPRINT__KEY_VERSION`.
- Do not rotate the active key until every retained idempotency record produced with the old key
  has expired or been deleted. Without a retained versioned keyring, a different key version is a
  conflict rather than a replay match.
- This pre-production service does not retain compatibility with records created by the superseded
  v1 canonical format. Clear or reset those local idempotency records before deploying v2; there is
  no runtime dual-format path or schema migration that makes v1 records comparable with v2.
