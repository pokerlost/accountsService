# API errors

Central handlers serialize all supported failures as `PokerlostResponse[None]` without raw input or
internal state.

## Runtime mappings

| Source | Status | Stable error |
| --- | --- | --- |
| Missing/malformed bearer authentication | `401` | `POKERLOST_AUTHENTICATION_REQUIRED` |
| Invalid access token or audience | `401` | `POKERLOST_ACCESS_TOKEN_INVALID` |
| Expired access token | `401` | `POKERLOST_ACCESS_TOKEN_EXPIRED` |
| Missing exact scope | `403` | `POKERLOST_INSUFFICIENT_SCOPE` |
| Request validation | `422` | `ACCOUNTSSERVICE_VALIDATION_ERROR` |
| Application not found | `404` | `ACCOUNTSSERVICE_NOT_FOUND` |
| Application conflict | `409` | `ACCOUNTSSERVICE_CONFLICT` |
| Invalid application operation | `422` | `ACCOUNTSSERVICE_INVALID_OPERATION` |
| Temporary application failure | `503` | `ACCOUNTSSERVICE_TEMPORARILY_UNAVAILABLE` |
| PostgreSQL unavailable | `503` | `ACCOUNTSSERVICE_DATABASE_UNAVAILABLE` |
| Other database failure | `500` | `ACCOUNTSSERVICE_DATABASE_ERROR` |
| Unexpected failure | `500` | `ACCOUNTSSERVICE_INTERNAL_ERROR` |

Framework not-found and method failures are also normalized. Public messages are fixed sanitized
text. Validation errors never echo submitted values.

An unavailable required verifier is a composition error and fails closed as an internal failure.
Concrete verifier adapters distinguish invalid credentials from expiration; unexpected verifier
failures remain internal instead of being mislabeled as caller failures. Authentication rejection
occurs before endpoint execution.

`retry_after` is finite non-negative seconds carried only in the JSON envelope by an explicitly
retryable application error. It is null for all other failures and every success.
