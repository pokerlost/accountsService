# API errors

Central handlers serialize all supported failures as `PokerlostResponse[None]` without raw input or
internal state.

## Runtime mappings

| Source | Status | Stable error |
| --- | --- | --- |
| Missing/malformed body authentication | `401` | `AUTHENTICATION_REQUIRED` |
| Invalid access token or audience | `401` | `INVALID_ACCESS_TOKEN` |
| Missing exact scope | `403` | `INSUFFICIENT_SCOPE` |
| Request validation | `422` | `ACCOUNTSSERVICE_VALIDATION_ERROR` |
| Application not found | `404` | `ACCOUNTSSERVICE_NOT_FOUND` |
| Application conflict | `409` | `ACCOUNTSSERVICE_CONFLICT` |
| Invalid application operation | `422` | `ACCOUNTSSERVICE_INVALID_OPERATION` |
| PostgreSQL unavailable | `503` | `ACCOUNTSSERVICE_DATABASE_UNAVAILABLE` |
| Other database failure | `500` | `ACCOUNTSSERVICE_DATABASE_ERROR` |
| Unexpected failure | `500` | `ACCOUNTSSERVICE_INTERNAL_ERROR` |

Framework not-found and method failures are also normalized. Public messages are fixed sanitized
text. Validation errors never echo submitted values.

An unavailable required verifier is a composition error and fails closed as an internal failure.
Concrete verifier adapters map rejected tokens to `InvalidAccessTokenError`; unexpected verifier
failures remain internal instead of being mislabeled as caller failures.

`retry_after` is null unless a handler has an explicit safe retry delay. No retry guidance is
encoded outside the JSON envelope.
