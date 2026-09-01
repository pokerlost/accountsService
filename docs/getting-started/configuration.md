# Configuration

This page documents the generated service settings groups and their environment variable mapping.

`Settings` loads `.env` and process environment values with the `ACCOUNTSSERVICE_` prefix.
Nested fields use a double underscore, so the general form is:

```text
ACCOUNTSSERVICE_<GROUP>__<FIELD>
```

For example, `database.url` maps to `ACCOUNTSSERVICE_DATABASE__URL`. Names are
case-insensitive, but `.env.example` uses uppercase names consistently. Process environment values
override values from `.env` according to Pydantic Settings behavior.

## Base operations

| Field | Environment variable | Required | Example |
| --- | --- | --- | --- |
| `root_operation` | `ACCOUNTSSERVICE_ROOT_OPERATION` | Yes | `accounts.getRoot` |
| `openapi_operation` | `ACCOUNTSSERVICE_OPENAPI_OPERATION` | Yes | `openapi.get` |

Both fields use `pypokerlost.types.APIOperation`, so invalid startup values fail validation. The
root operation controls only the operation ID for `GET /`; the HTTP path remains `/`. The OpenAPI
operation controls both its operation ID and its `"/" + operation_id` path. Business operation IDs
remain source-defined stable contracts rather than environment settings.

The Helm values `rootOperation` and `openapiOperation` map explicitly to those exact two
environment variables in the ConfigMap. They are not Kubernetes Secrets.

## `application`

| Field | Environment variable | Purpose |
| --- | --- | --- |
| `environment` | `ACCOUNTSSERVICE_APPLICATION__ENVIRONMENT` | Deployment category such as `local`, `development`, `staging`, or `production`. |
| `version` | `ACCOUNTSSERVICE_APPLICATION__VERSION` | SemVer service contract version published in OpenAPI and telemetry. |

Production configuration fails at startup unless Logfire and remote delivery are enabled.

## `http`

| Field | Environment variable | Purpose |
| --- | --- | --- |
| `host` | `ACCOUNTSSERVICE_HTTP__HOST` | Local HTTP bind address. |
| `port` | `ACCOUNTSSERVICE_HTTP__PORT` | Local HTTP port from `1` through `65535`. |

## `database`

| Field | Environment variable | Purpose |
| --- | --- | --- |
| `url` | `ACCOUNTSSERVICE_DATABASE__URL` | Required complete `postgresql+asyncpg` SQLAlchemy URL. |
| `pool_size` | `ACCOUNTSSERVICE_DATABASE__POOL_SIZE` | Persistent connection-pool size. |
| `max_overflow` | `ACCOUNTSSERVICE_DATABASE__MAX_OVERFLOW` | Additional temporary connections allowed above the pool size. |
| `pool_timeout_seconds` | `ACCOUNTSSERVICE_DATABASE__POOL_TIMEOUT_SECONDS` | Maximum wait for a pooled connection. |
| `command_timeout_seconds` | `ACCOUNTSSERVICE_DATABASE__COMMAND_TIMEOUT_SECONDS` | Asyncpg command timeout. |

The database URL must include a username, password, host, and database. It is treated as a secret and must not appear in logs or committed files.

## `logfire`

| Field | Environment variable | Purpose |
| --- | --- | --- |
| `enabled` | `ACCOUNTSSERVICE_LOGFIRE__ENABLED` | Enable Logfire configuration and instrumentation. |
| `send_to_logfire` | `ACCOUNTSSERVICE_LOGFIRE__SEND_TO_LOGFIRE` | Send telemetry to the configured remote project. |
| `console` | `ACCOUNTSSERVICE_LOGFIRE__CONSOLE` | Render telemetry to the process console. |
| `minimum_level` | `ACCOUNTSSERVICE_LOGFIRE__MINIMUM_LEVEL` | Minimum recorded level. |
| `token` | `ACCOUNTSSERVICE_LOGFIRE__TOKEN` | Optional write token, required when remote delivery is enabled. |

## `business_operation_fingerprint`

| Field | Environment variable | Default/bounds | Purpose |
| --- | --- | --- | --- |
| `secret` | `ACCOUNTSSERVICE_BUSINESS_OPERATION_FINGERPRINT__SECRET` | Required; at least 32 UTF-8 bytes | Dedicated HMAC-SHA-256 key for resumable operation payload fingerprints. |
| `key_version` | `ACCOUNTSSERVICE_BUSINESS_OPERATION_FINGERPRINT__KEY_VERSION` | `1`; integer at least `1` | Version persisted beside every fingerprint digest. |

The secret is mandatory because accountsService owns active idempotent workflows. Only digest and
key version are persisted. Do not rotate the active key until every retained record made with the
old key has expired or been deleted; the current key-rotation policy intentionally has no
overlapping keyring. Records produced by the superseded pre-production canonical format must be
cleared before v2 is enabled; there is no dual-format comparison path.

## `password`

| Field | Environment variable | Default | Valid range |
| --- | --- | --- | --- |
| `argon2_memory_cost` | `ACCOUNTSSERVICE_PASSWORD__ARGON2_MEMORY_COST` | `65536` KiB | `8192` through `1048576` |
| `argon2_time_cost` | `ACCOUNTSSERVICE_PASSWORD__ARGON2_TIME_COST` | `3` | `1` through `20` |
| `argon2_parallelism` | `ACCOUNTSSERVICE_PASSWORD__ARGON2_PARALLELISM` | `4` | `1` through `16` |
| `argon2_hash_length` | `ACCOUNTSSERVICE_PASSWORD__ARGON2_HASH_LENGTH` | `32` bytes | `16` through `128` |
| `argon2_salt_length` | `ACCOUNTSSERVICE_PASSWORD__ARGON2_SALT_LENGTH` | `16` bytes | `16` through `64` |
| `min_length` | `ACCOUNTSSERVICE_PASSWORD__MIN_LENGTH` | `12` characters | `1` through `1024` |
| `max_length` | `ACCOUNTSSERVICE_PASSWORD__MAX_LENGTH` | `256` characters | `1` through `4096` |

The minimum must not exceed the maximum. Password length counts the exact Python string input;
accountsService does not trim or normalize it. One lifespan-owned `Argon2PasswordService` uses all
seven values for validation, hashing, dummy verification, and rehash-policy checks.

Keep the fingerprint secret, Logfire token, and database URL outside source control. Kubernetes
supplies them through Secret references rather than the chart ConfigMap; see
`docs/development/containers-and-kubernetes.md`.

## Outbound service targets

The current settings model has no authService target group because no implemented operation calls
authService. Consequently there are no `ACCOUNTSSERVICE_AUTH_SERVICE__*` environment variables,
client credentials, requested scopes, token storage, or retry settings. Do not preconfigure an
unused target.

When a concrete operation introduces that dependency, add one focused immutable authService
settings group and one explicitly named field on root `Settings`. Its base URL and request timeout
are deployment configuration. Token credentials, storage, refresh, requested exact scopes, and
audience remain service-owned and are added only when the implemented use case needs them.

Do not expose `PokerLostRetryPolicy` values as settings; its transport algorithm is fixed by the
SDK. Do not automatically add authService configuration to every service. The complete ownership
pattern is in `docs/architecture/inter-service-clients.md`.
