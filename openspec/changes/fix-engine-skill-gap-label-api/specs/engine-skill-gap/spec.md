# engine-skill-gap

## ADDED Requirements

### Requirement: a spawned tracking issue is labelled through the REST API

`scripts/engine_skill_gap.py::open_issue` MUST apply the issue's labels with
`POST repos/<repo>/issues/<n>/labels` (`gh api -X POST … -f labels[]=<name>`) and MUST NOT pass
`--label` to `gh issue create`. The create's `--label` is silently dropped on the runner path, so an
issue created that way exists and is invisible to `scripts/issue_implementer.py`, which selects on
`agent:implement`.

WHEN the spawn step files a tracking issue for an unresolved registry engine
THEN it creates the issue, then labels it `bug` and `agent:implement` through the REST label
endpoint, so the issue lands in the bots' queue.

#### Scenario: a created issue is labelled by the API, not by create's flag

- **Given** a registry naming one engine llgenie does not ship, and a `gh` whose `issue create` stores no label
- **When** `engine_skill_gap.py spawn` runs
- **Then** exactly one `gh api -X POST repos/acme/llgenie/issues/501/labels` call carries
  `labels[]=agent:implement`
- **And** the create call passes no `--label`
- **Test:** `tests/test_engine_skill_gap.py::test_spawn_opens_one_issue_per_unresolved_engine_with_real_evidence`

### Requirement: the label is read back and a missing queue label fails the step

`scripts/engine_skill_gap.py` MUST read the labels back from the same REST endpoint
(`GET repos/<repo>/issues/<n>/labels --jq .[].name`) after every label write, and MUST fail the step
with a message naming the issue and the missing label when a label did not stick. A green run whose
tracking issue carries no `agent:implement` is indistinguishable from success while the work routes
to nobody.

WHEN the label write succeeds but the read-back does not contain `agent:implement`
THEN the spawn step exits non-zero, naming the issue number and the label.

#### Scenario: a label that does not stick is a red step

- **Given** a `gh` whose label POST is accepted but never stored
- **When** `engine_skill_gap.py spawn` runs
- **Then** the POST was attempted first
- **And** the command exits 1, and its stderr names `agent:implement` and the issue number
- **Test:** `tests/test_engine_skill_gap.py::test_a_tracking_issue_that_cannot_be_labelled_fails_the_step_naming_it`

#### Scenario: a labelled issue is proved by reading it back

- **Given** a `gh` that keeps the labels it is POSTed
- **When** `engine_skill_gap.py spawn` runs
- **Then** the created issue's labels are read back through
  `repos/acme/llgenie/issues/501/labels --jq .[].name`
- **And** the read-back contains `agent:implement`
- **And** no `gh issue edit` or `gh issue view` GraphQL call is made
- **Test:** `tests/test_engine_skill_gap.py::test_a_spawned_tracking_issue_lands_in_the_bots_queue`

### Requirement: the change issue the sync files is labelled the same way

`scripts/registry_change_issue.py::open_issue` MUST NOT pass `--label` to `gh issue create` and MUST
apply `agent:implement` with `POST repos/<repo>/issues/<n>/labels`, then read it back and fail the
step — naming the issue — when it is absent. The create path MUST take the issue number from the
create URL and abort when the URL carries none. The marker-dedupe path MUST re-label an existing issue
that carries the marker but lost the label, and a `--dry` run MUST write nothing.

WHEN the weekly sync files or updates the store-change issue
THEN the issue carries `agent:implement`, proved by reading the labels back, on the host and in CI.

#### Scenario: the change issue is created unlabelled by the flag and labelled by the API

- **Given** a changed store with no open issue carrying the marker
- **When** `open_issue()` runs
- **Then** the create call passes no `--label`
- **And** exactly one `POST repos/asimov-agent/llgenie/issues/705/labels` carries
  `labels[]=agent:implement`
- **And** the labels of #705 are read back from the tracker
- **Test:** `tests/test_registry_change_issue.py::test_a_store_with_no_open_issue_creates_exactly_one`

#### Scenario: a marked issue that lost its label is re-queued, not duplicated

- **Given** an open issue #704 carrying the store's marker and no label
- **When** `open_issue()` runs for that store
- **Then** it edits #704 and creates no second issue
- **And** `POST repos/asimov-agent/llgenie/issues/704/labels` carries `labels[]=agent:implement`
- **Test:** `tests/test_registry_change_issue.py::test_a_second_open_for_the_same_store_updates_instead_of_duplicating`

#### Scenario: a change issue that cannot be labelled is a red step

- **Given** a tracker whose label write is accepted but never stored
- **When** `open_issue()` runs
- **Then** it exits non-zero, naming the issue number and `agent:implement`
- **And** the POST was attempted before the failure
- **Test:** `tests/test_registry_change_issue.py::test_a_change_issue_that_cannot_be_labelled_fails_the_step`

### Requirement: an existing tracking issue that lost its queue label is repaired

`ensure_queue_label` MUST repair an already-open tracking issue that does not carry
`agent:implement`, through the same REST POST + read-back, and MUST NOT open a duplicate issue.

WHEN a tracking issue for the unresolved engine is already open and unlabelled
THEN the step labels that issue `agent:implement` and creates nothing.

#### Scenario: an unlabelled open issue is re-queued, not duplicated

- **Given** an open tracking issue #42 for the unresolved engine, carrying no queue label
- **When** `engine_skill_gap.py spawn` runs
- **Then** no issue is created
- **And** `POST repos/acme/llgenie/issues/42/labels` carries `labels[]=agent:implement`
- **Test:** `tests/test_engine_skill_gap.py::test_spawn_is_idempotent_and_creates_nothing_for_a_decided_engine`
