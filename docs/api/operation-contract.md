# Operation contract

Pokerlost business APIs use one private JSON operation protocol over HTTPS.

## Operations and paths

Every business operation matches:

```text
operation_id = lowerCamelCase verb name
path         = "/" + operation_id
HTTP method  = POST
```

The exact identifier pattern is `^[a-z][A-Za-z0-9]*$`. Valid examples include `getMe`,
`registerAccount`, and `provisionHuman`. Dots, underscores, hyphens, and uppercase initials are
invalid. The generator validates all source documents together and rejects global operation or
schema collisions before writing.

`GET /`, `GET /getOpenApi`, and existing health probes are public bodyless infrastructure
exceptions. Business GET bodies and other business HTTP methods are unsupported.

Each static route is one flat module with a module-level `router = APIRouter(...)` and a
module-level decorated endpoint. Do not use router factories, nested endpoints, nested router
directories, imperative registration, one-use route constants, or post-hoc mutation.

## Requests

Every operation accepts `PokerlostRequest[Payload]`:

```json
{
  "payload": {
    "username": "alice"
  }
}
```

Payload types are named closed Pydantic models with snake_case wire fields. Requests do not use
business path/query parameters, cookies, form data, caller-supplied transport metadata, embedded
anonymous bodies, or manual content negotiation.

Pydantic request models parse and validate primitive wire input, including UUIDs and enums. Route
modules do not duplicate that boundary with `_parse_*` helpers; routes only map validated values
to application commands or queries.

A protected operation additionally requires `Authorization: Bearer <access-token>`. The bearer
value never becomes part of the JSON schema or application payload.

## Responses

Every business success and handled failure uses the `PokerlostResponse` wire contract. A normal
route declares its typed envelope as `response_model` and returns plain Python data for FastAPI to
validate and serialize. Typed failures flow through centralized exception handling, which alone
constructs `PokerlostResponse[None]` and a `JSONResponse`. The raw OpenAPI publication endpoint is
an infrastructure exception. The five-field invariant is documented in
`docs/api/pokerlost-response.md`.

## Scopes

Scope IDs are separate from operation IDs. Protected routes declare exact values through FastAPI
`Security`, while the matching SDK method declares the same non-empty `__scopes__` tuple. A public
method declares `__scopes__ = None`; an empty tuple is invalid. See
`docs/api/header-authorization.md`.
