# Header authorization

Protected Pokerlost operations accept an access token only through the standard HTTP
`Authorization` header.

## Request boundary

```text
Authorization: Bearer <access-token>
Content-Type: application/json
```

The JSON body remains the pure operation envelope:

```json
{
  "payload": {}
}
```

It contains no token, authorization object, headers map, or execution metadata. Missing headers,
non-bearer schemes, empty credentials, and credentials containing whitespace are authentication
failures.

## Local verifier seam

`app/application/ports/pokerlost_token_verifier.py` defines the transport-independent
`PokerlostTokenVerifier`. It receives a representation-safe `SecretStr` and the exact
`PokerlostAudience("accountsService")`. A concrete local adapter verifies signature, time claims,
revocation state and audience without making a per-request authService call. It returns a
scope-only `PokerlostAuthorizationContext` or raises the canonical invalid/expired application
error before the endpoint handler starts.

The current service has no protected route and therefore configures no concrete verifier. Future
protected composition fails closed if a verifier is missing.

## Route composition

```python
from typing import Annotated

from fastapi import APIRouter, Security
from pypokerlost.types import (
    PokerlostAuthorizationContext,
    PokerlostRequest,
    PokerlostResponse,
)

from api.dependencies import authorize_pokerlost_request
from domain.enums import Scopes


router = APIRouter(tags=["accounts"])


@router.post(
    path="/getMe",
    operation_id="getMe",
    response_model=PokerlostResponse[GetMeResponse],
)
async def get_me(
    request: PokerlostRequest[GetMeRequest],
    authorization: Annotated[
        PokerlostAuthorizationContext,
        Security(
            authorize_pokerlost_request,
            scopes=[Scopes.SELF_GET_ME],
        ),
    ],
) -> dict[str, object]:
    result = await handle_get_me(request.payload, authorization)
    return {"ok": True, "result": result}
```

`app/domain/enums/scopes.py` owns the local `Scopes` catalog. Every protected operation declares at
least one exact member. Public operations omit the dependency entirely; an empty protected
requirement is a configuration error. Pydantic request models parse UUIDs, enums, audiences and
other primitive wire values before the route maps them into an application command.

The endpoint returns plain data. FastAPI validates and serializes it through `response_model`;
normal endpoints do not instantiate `PokerlostResponse` or `JSONResponse`.

## Standard OpenAPI metadata

The dependency uses FastAPI's `OAuth2` model with a client-credentials flow, `tokenUrl` set to
`/getToken`, and `auto_error=False`. A protected route therefore publishes the full catalog under
`components.securitySchemes` and its exact required members under the POST operation's `security`
array. No manual route metadata or document rewriting is used.

Because the current HTTP surface has no protected operation, its present OpenAPI document has no
security requirement or unused security component. That is a valid production document and does
not require a fake route, injected component, custom extension or scope map.

## Failures

Missing/malformed authentication maps to `POKERLOST_AUTHENTICATION_REQUIRED`, invalid credentials
or audience to `POKERLOST_ACCESS_TOKEN_INVALID`, expiration to
`POKERLOST_ACCESS_TOKEN_EXPIRED`, and a missing capability to `POKERLOST_INSUFFICIENT_SCOPE`.
Every failure uses the central `PokerlostResponse` serializer, and none enters the handler.

FastAPI instrumentation captures neither request bodies nor headers. Errors, logs and spans never
contain the bearer value.
