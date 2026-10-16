# The agent-image push pre-flight (#335)

## Why

`publish-agent-image.yml` allows 60 minutes and went straight from the GHCR login to
`make publish-agent-image`, where the build is the costly part. The verdict it could not afford to learn
late — whether the credential may write the package at all — is available in seconds from the registry.

`README.md` documented `make agent-image-push-check` as if it existed; `grep -n "push-check" Makefile`
found nothing. #323/#336 corrected the prose to say "not implemented … Tracked as issue #335"; this change
builds it.

## What landed

- `scripts/ci_images.py pushcheck <name>`: `GET /token?service=<host>&scope=repository:<owner>/llgenie/<name>:push`
  under Basic auth from `GHCR_USER`/`GHCR_TOKEN`, then `POST /v2/<path>/blobs/uploads/` with the issued
  `Bearer` token and **no body**. An empty upload is the cheapest real write there is: a refusal costs
  nothing and a success leaves no layer. Any 2xx = may push; anything else prints the registry's own
  message and exits 1. `urllib.error.HTTPError` is returned as data, so a 403 surfaces as the registry's
  message rather than as a traceback that hides it.
- `make agent-image-push-check` — `.PHONY`, a `make help` line, README-documented, and it refuses to run
  without `GHCR_TOKEN` so a misconfigured dispatch fails instead of silently passing.
- `publish-agent-image.yml` runs it as its own step **before** the publish, handed
  `GHCR_TOKEN: ${{ secrets.BUMP_TOKEN }}` (the same credential the login uses, measured against the
  workflow's own `docker login`). The `Flow:` header names the new stage, so the #323 guard — every
  `Flow:` target must resolve — keeps holding.
- `package(name)` derives `(base URL, package path)` from `LLGENIE_REGISTRY`: `ghcr.io/asimov-agent` →
  `https://ghcr.io` + `asimov-agent/llgenie/agent`; a bare host (the test stub) → `llgenie/agent`.

## Verification

- `tests/test_ci_images.py`: **25 passed** in `llgenie/test:latest` (8 new). No mocks: a stub registry on
  `127.0.0.1` records `(method, path, authorization)`, so the token scope, the Basic credential and the
  `Bearer` upload are asserted as the actual HTTP shape.
- Falsified: making the denial return 0 fails `test_pushcheck_fails_when_the_credential_may_not_push`
  (`assert 0 == 1`), so the test locks the behaviour rather than the implementation.
- The target run by hand against a local stub:
  `LLGENIE_REGISTRY=http://127.0.0.1:8731 GHCR_TOKEN=… make agent-image-push-check` → **rc 0**, and the
  registry logged `GET /token?…&scope=repository:llgenie/agent:push` then
  `POST /v2/llgenie/agent/blobs/uploads/`; with the stub answering the upload 403 the same command exits
  non-zero quoting `denied: requested access to the resource is denied`. With no `GHCR_TOKEN` at all it
  exits non-zero on the target's own check, before contacting anything.
- A request that never got an answer (DNS, refused connection, timeout) comes back as status 0 and is
  reported as `could not reach <registry>` — a failure path must not arrive as a traceback.
- `make lint`, `make check-docs`, `make check-wiring`, `make check-workflows`, `make check-dispatch-forms`,
  `make openspec-validate NAME=agent-image-push-check`.

## Note

The pre-flight is proven against a stub, not against GHCR: the real verdict needs the owner PAT and a
dispatch of `publish-agent-image.yml`, which `gh workflow run --ref <branch>` refuses with `422: No ref
found` for a fork-only branch. So the effective evidence until this merges is the HTTP shape the stub
records plus the workflow wiring — say that plainly rather than implying a live GHCR push was proven.

Refs: #323 (the `Flow:`-target guard that surfaced the missing target), #336 (the PR that corrected the
prose), #117/#222/#238/#248 (the CI images and the agent publish path), #331 (the fix that made the
workflow run again).
