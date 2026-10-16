# API errors

The current HTTP handlers use `PokerlostResponse[None]` with fixed safe messages. They do not echo input, database errors, tokens or exception text.

| Source | Status | Stable error |
| --- | --- | --- |
| Missing or malformed bearer authentication | `401` | `POKERLOST_AUTHENTICATION_REQUIRED` |
| Invalid token or audience | `401` | `POKERLOST_ACCESS_TOKEN_INVALID` |
| Missing exact scope | `403` | `POKERLOST_INSUFFICIENT_SCOPE` |
| Request validation | `422` | `ACCOUNTSSERVICE_VALIDATION_ERROR` |
| Unknown route | `404` | `ACCOUNTSSERVICE_NOT_FOUND` |
| Unsupported method | `405` | `ACCOUNTSSERVICE_METHOD_NOT_ALLOWED` |
| Required database unavailable | `503` | `ACCOUNTSSERVICE_DEPENDENCY_UNAVAILABLE` |
| Unexpected error | `500` | `ACCOUNTSSERVICE_INTERNAL_ERROR` |

No protected or business operation is currently registered. A future verifier must distinguish expiry from invalid credentials without exposing secrets. A missing real verifier fails closed. The SDK's future-facing error types do not imply an implemented server route.
