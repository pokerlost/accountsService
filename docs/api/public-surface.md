# Public surface

This is the endpoint manifest for the current `accountsService` HTTP surface. The account,
password and resumable-workflow foundations are not yet exposed as business routes.

| Method and path | `operation_id` | Request | Response |
| --- | --- | --- | --- |
| `GET /` | `getRoot` | No body or authentication | `PokerlostResponse[None]` |
| `GET /getOpenApi` | `getOpenApi` | No body or authentication | Raw OpenAPI JSON document |

The root response is:

```json
{
  "ok": true,
  "result": null,
  "error": null,
  "error_message": null,
  "retry_after": null
}
```

Neither endpoint proves database readiness or contains business behavior. `/getOpenApi` returns
`request.app.openapi()` without an additional response envelope. Liveness/readiness probes use `/`
only as process availability.

A concrete service records every implemented business route here with its exact POST path,
operation ID, public/protected contract, typed result, statuses and required scopes. Planned SDK
stubs are not documented as active server endpoints.

The service-owned capability catalog is not an implemented HTTP surface. With no protected route,
the current OpenAPI paths contain no security requirement and no unused OAuth2 component.
