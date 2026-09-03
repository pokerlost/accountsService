# API overview

The service uses FastAPI with the Pokerlost JSON protocol over HTTPS and standard bearer
authorization for protected operations.

Every business operation is `POST /<operationId>` with one lowerCamelCase verb name. Every body
uses the pure `PokerlostRequest` envelope. Protected input adds an `Authorization: Bearer` header;
business results use the `PokerlostResponse` wire contract. Normal routes return plain data for
FastAPI to validate and serialize through their declared `response_model`.

`GET /` and `GET /getOpenApi` are public bodyless infrastructure endpoints. The root uses the
canonical envelope, while `/getOpenApi` returns the raw generated document. The current service
contains no business route or concrete token verifier; its account/password domain, capability
catalog and persistence foundation remain internal until an application flow is implemented.

Read `docs/api/operation-contract.md` for operation rules,
`docs/api/pokerlost-response.md` for the response invariant,
`docs/api/header-authorization.md` for exact scopes and local verification, and
`docs/api/openapi-and-sdk.md` for publication/generation.
