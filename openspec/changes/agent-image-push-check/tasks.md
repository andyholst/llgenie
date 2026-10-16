# Tasks

- [x] 1. `scripts/ci_images.py pushcheck <name>`: push-scoped token exchange, then an empty blob upload against `<owner>/llgenie/<name>`, with the registry's own refusal printed and a non-zero exit; an HTTP error is data, never a traceback
- [x] 2. `make agent-image-push-check` exists, is in `.PHONY`, has a `make help` line and is documented in README; it refuses to run without `GHCR_TOKEN`
- [x] 3. `publish-agent-image.yml` runs the pre-flight as its own make step BEFORE `make publish-agent-image`, handed `GHCR_TOKEN: secrets.BUMP_TOKEN`; its `Flow:` header names the new stage so the #323 guard (every `Flow:` target exists) holds
- [x] 4. Tests in `tests/test_ci_images.py`, no mocks: a stub registry on `127.0.0.1` records the requests, so the token `scope=repository:llgenie/agent:push` and the empty upload's `Bearer` token are asserted as the real HTTP shape
- [x] 5. Falsified: with the denial swallowed (the step returns 0 for a 403) `test_pushcheck_fails_when_the_credential_may_not_push` fails — `assert 0 == 1` — proving the test locks the behaviour, not the implementation. 8 new tests, **25 passed** in `tests/test_ci_images.py`
- [x] 6. Every failure path covered: a refused token fails with no upload attempted; a missing `GHCR_TOKEN` fails before any request; an unreachable registry fails with a sentence rather than a traceback; with no `GHCR_USER` the Basic user is the registry's owner (and the owner lands in the package path); the workflow test pins the step ORDER and the credential hand-off
- [x] 7. The make target exercised end-to-end against a local stub registry: `rc=0` and the two requests the registry logged when it may push, and a non-zero exit quoting `denied: requested access to the resource is denied` when the upload is refused
- [x] 8. README's agent-image paragraph describes what the target really does (#335's "not implemented" note is gone); `agent-wiki/2026-10-16-agent-image-push-check.md` records the work
- [x] 9. `make lint`, `make check-docs`, `make check-wiring`, `make check-workflows`, `make check-dispatch-forms` and `make openspec-validate NAME=agent-image-push-check` exit 0
