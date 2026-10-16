# agent-image-push-check

## ADDED Requirements

### Requirement: the publish proves the credential can push BEFORE the expensive build

`publish-agent-image.yml` MUST run a push pre-flight as its own make step, BEFORE the step that builds and
publishes, and MUST hand it the same credential the job logs in with. `make agent-image-push-check` MUST
exist as a Makefile target that is `.PHONY`, carries a `make help` line, is documented in `README.md`, and
refuses to run without that credential.

WHEN the agent-image publish job starts its publish work
THEN the pre-flight runs first, and a credential that cannot push stops the run before the build.

#### Scenario: the pre-flight precedes the build in the publish job

- **Given** the `publish` job of `publish-agent-image.yml` and the Makefile
- **When** the job's steps are read
- **Then** the step that runs `make agent-image-push-check` comes before the step that runs `make publish-agent-image`
- **And** the pre-flight step is handed `GHCR_TOKEN`
- **And** `agent-image-push-check` is a Makefile target, is in `.PHONY`, and runs the pushcheck sub-command
- **Test:** `tests/test_ci_images.py::test_the_publish_job_proves_the_push_before_it_builds`

### Requirement: the pre-flight asks for a push-scoped token and writes nothing

The pre-flight MUST ask the registry for a **push-scoped token** for the package the publish writes
(`<owner>/llgenie/<name>` under the configured registry), and then initiate an **empty** blob upload —
no data, so a refusal costs nothing and a success leaves no layer. It MUST NOT pull, build, tag or push
an image.

WHEN the pre-flight runs against a registry that grants the token
THEN it requests `scope=repository:<package>:push`, then POSTs to `/v2/<package>/blobs/uploads/` with the
token it was just issued, and sends no body.

#### Scenario: a push-scoped token, then an empty upload

- **Given** a registry that grants a push-scoped token and accepts the upload
- **When** the pre-flight runs for the agent package
- **Then** it exits 0, and the requests it made were `GET /token` with
  `scope=repository:llgenie/agent:push` under Basic auth, then
  `POST /v2/llgenie/agent/blobs/uploads/` with `Bearer <the token it was issued>`
- **And** the package path carries the registry's owner when the registry names one (`ghcr.io/asimov-agent`
  → `asimov-agent/llgenie/agent`), over https
- **And** with no `GHCR_USER` the Basic user is that same owner segment — the account the workflow's own
  `docker login -u ${{ github.repository_owner }}` uses
- **Test:** `tests/test_ci_images.py::test_pushcheck_asks_for_a_push_token_then_does_an_empty_upload`,
  `tests/test_ci_images.py::test_the_push_check_targets_the_package_the_publish_writes` and
  `tests/test_ci_images.py::test_pushcheck_defaults_to_the_registry_owner_and_targets_its_package`

### Requirement: a refusal is the registry's, and it fails the step

A credential that may not push MUST fail the step non-zero, and the registry's own message MUST be
surfaced. A denial MUST NOT be swallowed into a green step — the whole point is that the run stops in
seconds instead of after a build that could never succeed. A run with no credential MUST fail before any
request is made.

WHEN the registry refuses the push-scoped token, or refuses the upload
THEN the pre-flight exits non-zero and prints the registry's message.

#### Scenario: a denied upload fails loudly

- **Given** a registry that grants the token but answers the upload with 403 and
  `denied: requested access to the resource is denied`
- **When** the pre-flight runs
- **Then** it exits 1, prints `CANNOT push` with the registry's message, and prints no success line
- **And** a registry that refuses the token exchange (403) fails the same way, having attempted no upload
- **And** with no credential in the environment it fails with `no credential`, contacting no registry
- **And** a registry that cannot be reached fails with a sentence naming it, not with a traceback
- **Test:** `tests/test_ci_images.py::test_pushcheck_fails_when_the_credential_may_not_push`,
  `tests/test_ci_images.py::test_pushcheck_reports_a_refused_token`,
  `tests/test_ci_images.py::test_pushcheck_without_a_credential_fails_before_any_request` and
  `tests/test_ci_images.py::test_pushcheck_fails_with_a_sentence_when_the_registry_is_unreachable`
