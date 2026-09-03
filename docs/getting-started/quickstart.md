# Quickstart

Start `accountsService` locally and inspect its two public infrastructure endpoints.

## Run

```bash
cp .env.example .env
uv lock
uv sync --locked
make run
```

Local development may bind the loopback HTTP server. Production access requires HTTPS/TLS and
must not expose this development listener directly.

## Root

```bash
curl --fail-with-body http://127.0.0.1:8000/
```

```json
{
  "ok": true,
  "result": null,
  "error": null,
  "error_message": null,
  "retry_after": null
}
```

## OpenAPI

```bash
curl --fail-with-body http://127.0.0.1:8000/getOpenApi
```

The response is the unmodified FastAPI OpenAPI document. Because the service has zero protected
operations, the document contains neither a security requirement nor an unused security scheme.

The current service exposes no business operation. Before adding one, read
`docs/api/operation-contract.md`, `docs/api/header-authorization.md`, and
`docs/api/pokerlost-response.md`.
