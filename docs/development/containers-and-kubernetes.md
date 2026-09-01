# Containers and Kubernetes

This page documents the generated Docker image and Helm chart workflows without treating them as an application deployment system.

## Docker build

The builder resolves the pinned private `pypokerlost` Git source. BuildKit therefore requires an authorized SSH agent and a trusted GitHub `known_hosts` entry:

```bash
ssh-add -l
ssh-keygen -F github.com
make docker-build
```

`make docker-build` forwards the agent with `--ssh default` and mounts `$HOME/.ssh/known_hosts` as the `github_known_hosts` build secret. The Dockerfile marks both inputs as required. Do not copy a private key into the build context, image, `.env`, or chart values, and do not disable host verification.

The multi-stage image installs build-only Git and SSH tooling in the builder. The Python 3.14
runtime contains the locked application environment, runs as numeric user and group `10001`, and
starts Gunicorn with Uvicorn workers. GitHub credentials are not runtime inputs.

## Helm validation

The chart lives under `deploy/helm/accountsservice/`. Validate it locally with:

```bash
make helm-lint
make helm-template
```

These targets wrap `helm lint` and `helm template`; they do not install or upgrade a cluster release.

## Runtime configuration and probes

The Deployment exposes the HTTP container port and configures both liveness and readiness probes as `GET /`. The root endpoint does not require a database query, so it checks that the application process can serve its base response without turning the probe into a business operation.

The top-level Helm values `rootOperation` and `openapiOperation` map explicitly to
`ACCOUNTSSERVICE_ROOT_OPERATION` and
`ACCOUNTSSERVICE_OPENAPI_OPERATION` in the generated ConfigMap. Other non-secret
environment values, including the fingerprint key version and password/Argon2 policy, come from
the `environment` map. Database credentials, the required business-operation fingerprint secret,
and the optional Logfire token use `secretEnvironment` references to existing Kubernetes Secret
names and keys. Never place secret values in `environment`, a ConfigMap, a committed values file,
or rendered documentation.

The current chart has no authService target values or client-secret reference because the service
has no implemented authService call. When such a call is added, its non-secret typed settings use
the existing ConfigMap convention and only `ACCOUNTSSERVICE_AUTH_SERVICE__CLIENT_SECRET` uses
`secretEnvironment`. Authorization values and access tokens are runtime-only and must never appear
in chart values, rendered manifests, telemetry, or logs.

The pristine chart contains no outbound target, credential, token storage, or retry values. A
concrete service with a real target may add its base URL and request timeout through the existing
non-secret `environment` or explicit ConfigMap convention. Credential and token-store inputs remain
service-owned and are wired only when an implemented use case needs them; secrets use
`secretEnvironment` and existing Kubernetes Secret references. `PokerLostRetryPolicy` values never
become deployment settings. Authorization headers and tokens never become chart values, ConfigMap
data, logs, or rendered manifests. See `docs/architecture/inter-service-clients.md` for the
ownership and lifecycle pattern.

The chart also disables service-account token mounting, requests a non-root runtime, uses a read-only root filesystem, drops Linux capabilities, and mounts a bounded writable temporary volume. Review rendered output and environment-specific Secret references before deployment; successful linting and rendering do not prove cluster readiness or application correctness.
