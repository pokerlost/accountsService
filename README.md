# accountsService

`accountsService` is the local Pokerlost foundation for human accounts and password credentials.
It has infrastructure HTTP, configuration and persistence wiring, with no account model, password
implementation, or business route. Ownership and historical migration limits are in [SERVICE.md](SERVICE.md).

Read the [documentation index](docs/index.md) for the complete guide and `AGENTS.md` for normative engineering rules. Python
3.14 or newer is required.

## 🚀 Install

The mandatory private `pypokerlost` dependency requires GitHub SSH read access:

```bash
ssh-add -l
uv sync --locked
```

Supply `DATABASE_URL` through a private process environment when running. `.env.example` is
documentation; the app does not load `.env` automatically. `uv.lock` is committed.

## Run

```bash
DATABASE_URL='postgresql+asyncpg://user:password@127.0.0.1:5432/accountsservice' make run
```

## Base endpoints

| method | path | operation_id | response |
| --- | --- | --- | --- |
| `GET` | `/` | `getRoot` | `PokerlostResponse[None]` |
| `GET` | `/getOpenApi` | `getOpenApi` | Raw OpenAPI JSON document |
| `GET` | `/health/live` | Excluded from OpenAPI | Process liveness |
| `GET` | `/health/ready` | Excluded from OpenAPI | Database readiness or 503 |

These public infrastructure endpoints accept no body or authentication. Every business operation
uses `POST /<operationId>` and a typed `PokerlostRequest` JSON body. Protected operations accept an
access token only through `Authorization: Bearer <access-token>`.

The service retains an empty scope catalog and a local-verifier port, but no fake verifier,
outbound client, credential, token store, or retry configuration because no current route needs
them. See `docs/api/header-authorization.md` and
`docs/architecture/inter-service-clients.md`.

## Development and deployment

Run `make help` for the local tool interface. Regular quality entry points are:

```bash
make check
uv build
```

Production access requires HTTPS/TLS. The generated Helm ClusterIP is an internal target and must
remain behind trusted TLS termination.

The canonical Copier source URL and immutable ref are recorded in `.copier-answers.yml`; updates do not require a sibling template checkout.
The `src/accountsservice/` package is installed without a workspace `PYTHONPATH`.

Technical HTTP tests run in `make check`. Positive PostgreSQL readiness and migrations require disposable storage. CI source checks run on PRs without secrets; the private SDK build is gated by reviewed SHA and the approved solo-owner/full-SHA admission policy. The Dockerfile consumes the SDK token through a BuildKit secret.

## Tested foundation commands

The shared template owns `Makefile`, `tests/foundation/` and `deploy/chart/`. Project-owned tests,
settings, scopes and migration history survive updates. `make test-unit` reports isolated
coverage; `make test` also measures enabled integration before advisory report generation. Missing owned
paths remain visible in the report. `make build image verify` uses the canonical wheel
container graph and requires the separately approved SDK-only BuildKit secret.

`make chart-check chart` validates/packages the shared chart. `make deploy-local` and
`make undeploy-local` operate only the explicit disposable Kind contour. External deployment
requires an approved destination and tested image manifest digest. Private runtime CI requires
a full reviewed SHA and the SDK-only App approval gate; skipped runtime checks do not pass.

## Docker verification

`make source` parses the required frozen lock, checks formatting/lint and compiles source using
public Docker tools without installing the SDK. It does not verify runtime types or tests.
After approved SDK access, `make check build verify image` uses the canonical Docker graph;
provide the short-lived token only with `DOCKER_BUILD_ARGS='--secret id=sdk_token,env=SDK_APP_TOKEN'`.
`check` runs strict static checks and the enabled source suite once; a persistence source run requires an explicitly disposable `TEST_DATABASE_URL` and `QUALITY_NETWORK=host`; `verify` freshly tests the installed wheel and any
enabled disposable PostgreSQL profile, with separate `coverage/installed/` reports. `make coverage`
reads current source reports without rerunning tests. Below 100% warns; assertions, types,
build/configuration/access and invalid/stale report errors fail.

Private CI is separate owner-only manual dispatch: actor and triggering actor serrja, full SHA
identical to the branch SHA and `SDK_BUILD_REVIEWED_SHA`, and the existing SDK-only App with
Contents read solely on pypokerlost. This solo-writer policy is not a server reviewer gate;
reassess before adding a writer. The owner activates the existing CI-only PR #2 and provisions
App repository secrets. Ordinary source CI success does not verify B1; a skipped/failed private
job fails manual acceptance. These commands do not merge, release or deploy to a remote cluster.
