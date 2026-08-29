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
