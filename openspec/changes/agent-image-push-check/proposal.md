# agent-image-push-check — proposal

Issue: [#335](https://github.com/asimov-agent/llgenie/issues/335)

## Why

`publish-agent-image.yml` is `workflow_dispatch`-only, allows **60 minutes**, and goes straight from the
GHCR login to `make publish-agent-image` — where the build is the expensive part. The failure it cannot
afford is the one that was knowable in seconds: whether the credential is allowed to write the package at
all. `permission_denied: create_package` / `denied: … Create organization package` are verdicts the
registry will give up front, but today the job learns them after the build.

The capability was documented in `README.md` (`make agent-image-push-check`) but never implemented —
`grep -n "push-check" Makefile` found nothing. #323/#336 corrected that prose to say so; this change
builds the capability the prose promised.

## What Changes

- **`scripts/ci_images.py pushcheck <name>`**: ask the registry for a **push-scoped token**
  (`GET /token?service=<host>&scope=repository:<owner>/llgenie/<name>:push`, Basic auth from
  `GHCR_USER`/`GHCR_TOKEN`), then initiate the cheapest real write there is — a **POST to
  `/v2/<path>/blobs/uploads/` with no body**. No data is sent, so a refusal costs nothing and a success
  leaves no layer. Any 2xx means the credential may push; anything else prints the registry's own
  message and exits non-zero. An HTTP error is data here, never a traceback that hides the verdict.
- **`make agent-image-push-check`** (in `.PHONY`, with a `make help` line, documented in README):
  refuses to run without `GHCR_TOKEN` and drives the sub-command.
- **`publish-agent-image.yml` runs it before the build**: one make call per step, handed the same
  credential the login uses (`GHCR_TOKEN: secrets.BUMP_TOKEN`). Its `Flow:` header names the new stage,
  so the #323 guard (every `Flow:` target must exist) holds.
- **Tests** in `tests/test_ci_images.py`, no mocks: a stub registry on `127.0.0.1` records every request,
  so the token request's `scope=repository:<owner>/llgenie/agent:push` and the empty-upload request's
  `Bearer` token are asserted as the actual HTTP shape; a 403 on the upload and a 403 on the token are
  both proven to exit non-zero and to surface the registry's message; a missing credential fails before
  any request is made; and the workflow test pins the step's ORDER (check before publish) and its wiring.

## Not covered

- #329 — actionlint's shellcheck findings across the workflows, including this one.
- `make check-workflows` gaining the full actionlint rule set: that is #329's second bullet.
- The `Flow:`-target guard itself shipped in #323 (PR #336); this change only adds a stage to that line.

Refs: #117 (the hash-tagged CI images), #222/#238/#248 (the agent image and its publish path), #331 (the
`${{ ... }}` fix that made this workflow run again).
