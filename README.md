# accountsService

`accountsService` owns the account and credential domain defined in `SERVICE.md`. The current
foundation includes account/password models, resumable workflow persistence, a typed Argon2id
policy, the private Pokerlost body-only JSON protocol, observability, Docker, and Helm. Concrete
HTTP business operations are added only with their complete application flow.

Read `docs/index.md` for the complete guide and `AGENTS.md` for normative engineering rules. Python
3.14 or newer is required.

## Install

The mandatory private `pypokerlost` dependency requires GitHub SSH read access:

```bash
cp .env.example .env
ssh-add -l
ssh -T git@github.com
uv lock
uv sync --locked
```

Replace local placeholders in `.env`; never store secrets or private keys in the repository.

## Run

```bash
make run
```

## Base endpoints

| method | path | operation_id | response |
| --- | --- | --- | --- |
| `GET` | `/` | `getRoot` | `PokerlostResponse[None]` |
| `GET` | `/getOpenApi` | `getOpenApi` | `PokerlostResponse[dict[str, JSONValue]]` |

These public infrastructure endpoints accept no body or authentication. Every business operation
uses `POST /<operationId>` and a typed JSON body. Public calls use `PokerlostRequest`; protected
calls use `PokerlostAuthorizedRequest` with the token only in `authorization.access_token`.

The service includes an empty exact-scope catalog and a local-verifier port, but no fake verifier,
outbound client, credential, token store, or retry configuration because no current route needs
them. See
`docs/api/body-authorization.md` and `docs/architecture/inter-service-clients.md`.

## Development and deployment

Run `make help` for the local tool interface. Regular quality entry points are:

```bash
make check
make pre-commit
```

Production access requires HTTPS/TLS. The generated Helm ClusterIP is an internal target and must
remain behind trusted TLS termination.
