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

The infrastructure operation IDs `getRoot` and `getOpenApi` and their paths are stable code-defined
API contracts. They are not settings, environment variables, Helm values or ConfigMap entries.

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

Keep the Logfire token and database URL outside source control. Kubernetes supplies them through
Secret references rather than the chart ConfigMap; see
`docs/development/containers-and-kubernetes.md`.

## Outbound service targets

The current settings model has no authService target group because no implemented operation calls
authService. Consequently there are no `ACCOUNTSSERVICE_AUTH_SERVICE__*` environment variables,
client credentials, token storage, refresher, or retry settings. Do not preconfigure an unused
target.

When a concrete operation introduces that dependency, add one focused immutable authService
settings group and one explicitly named field on root `Settings`. Its base URL and request timeout
are deployment configuration. Credentials, explicit initial acquisition, encrypted shared storage,
refresh coordination, exact scopes and audience remain service-owned and are added only when the
implemented use case needs them.

Do not expose `PokerlostRetryPolicy` values as settings; its transport algorithm is fixed by the
SDK. Do not automatically add authService configuration to every service. The complete ownership
pattern is in `docs/architecture/inter-service-clients.md`.
