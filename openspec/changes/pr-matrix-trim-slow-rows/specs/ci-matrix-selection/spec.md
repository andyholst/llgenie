# ci-matrix-selection

## ADDED Requirements

### Requirement: Whether the heavy row runs is one decided value

The CI pipeline SHALL decide, in one place with a CLI (`scripts/ci_slow_rows.py`, run by
`make ci-slow-rows`), whether `linux / top-tier` runs in this run. A `pull_request` run SHALL
schedule it only when the PR carries the `ci:slow` label; every other event SHALL schedule it. Every
other row SHALL be unaffected.

WHEN a run starts
THEN `make ci-slow-rows` prints one `[ci-slow-rows]` line naming the event, the labels and the row's
state, and publishes the `top_tier_rows` key the workflow consumes.

#### Scenario: a pull request without the label schedules no heavy row

Given a `pull_request` event and a PR whose labels do not include `ci:slow`
When  the row selection is decided
Then  `top_tier_rows` is `["none"]`.

- **Test:** `tests/test_ci_slow_rows.py::test_a_pull_request_without_the_label_does_not_schedule_the_heavy_row`

#### Scenario: the label brings the row back

Given a `pull_request` event and a PR labelled `ci:slow`
When  the row selection is decided
Then  `top_tier_rows` is `["run"]`.

- **Test:** `tests/test_ci_slow_rows.py::test_the_ci_slow_label_brings_the_row_back`

#### Scenario: a non-PR event keeps the row

Given a `push` to `main` (or a dispatch, a schedule, or an event the script cannot classify)
When  the row selection is decided
Then  `top_tier_rows` is `["run"]`, so one run per merge still catches a model/engine regression.

- **Test:** `tests/test_ci_slow_rows.py::test_every_non_pull_request_event_keeps_the_row`

#### Scenario: an unrelated label does not opt a PR in

Given a pull request whose labels do not include `ci:slow`
When  the row selection is decided
Then  the row stays the placeholder, whatever else the PR carries.

- **Test:** `tests/test_ci_slow_rows.py::test_a_labelled_release_branch_run_is_still_a_pull_request`

### Requirement: The decision reaches the matrix, and a placeholder runs no work

`ci.yml` SHALL publish the decision from its `guard` job and the `linux` caller SHALL pass it in as
`top_tier_rows`; `pipeline.yml`'s `top-tier` job SHALL take that list as its ONE matrix axis. A row
that is not scheduled SHALL run no make target and SHALL print why it did nothing. No job-level
`if:` SHALL be used to remove a row.

WHEN a row is the `["none"]` placeholder
THEN no make target runs in it, its first step prints `[slow-rows] … = NOT SCHEDULED`, and the job's
check name stays visible.

#### Scenario: the output and the caller are wired

Given `.github/workflows/ci.yml`
When  the `guard` job's outputs and the `linux` caller are read
Then  the guard publishes `top_tier_rows` from the `make ci-slow-rows` step, and the caller passes it
into the shared `pipeline.yml`.

- **Test:** `tests/test_ci_slow_rows.py::test_ci_yml_publishes_the_decision_and_the_caller_consumes_it`

#### Scenario: an absent row does no work

Given `.github/workflows/pipeline.yml`
When  the `top-tier` job is read
Then  it has a single `row` axis from its input, no job-level `if:`, and every step that runs a make
target is gated on `matrix.row != 'none'`.

- **Test:** `tests/test_ci_slow_rows.py::test_the_top_tier_row_is_the_only_axis_and_runs_no_work_when_absent`

#### Scenario: no other row gained a gate

Given `pipeline.yml`'s `unit` and `cpu-health` jobs
When  they are read
Then  neither has a row axis or a placeholder step: `linux / unit` is still the PR gate for the
suite and `linux / cpu-health` still serves the model on a PR.

- **Test:** `tests/test_ci_slow_rows.py::test_the_other_rows_keep_their_pr_gates`

### Requirement: The coverage trade is written down, never silent

`docs/BOTS.md` SHALL state which row is main-only + opt-in, that the `ci:slow` label brings it back,
what it costs when requested, and what did not change; the `ci.yml` header SHALL carry the same
decision.

WHEN a reader opens the bot documentation or the workflow header
THEN the row, the label and the retained PR gates are named there, and the doc says the macOS rows
are gone by deletion (#870).

#### Scenario: the trade is documented

Given `docs/BOTS.md` and the `.github/workflows/ci.yml` header
When  they are searched for the decision
Then  both name `linux / top-tier` and `ci:slow`, and the doc names `linux / unit` and `cpu-health`
as retained PR gates and `#870` as the macOS deletion.

- **Test:** `tests/test_ci_slow_rows.py::test_the_coverage_trade_is_written_down`
