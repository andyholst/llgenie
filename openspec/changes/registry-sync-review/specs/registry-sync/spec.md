# registry-sync-review

## ADDED Requirements

### Requirement: the review only runs for a GREEN registry-sync PR

`make registry-review-brief` SHALL read the OPEN `chore/registry-sync` pull request and its checks, and
SHALL print `action=review` ONLY when the PR exists and every check's bucket is `pass`. A missing PR, a
`fail`, a `pending` or a `cancel` bucket SHALL print `action=skip` with the reason, and no
secret-spending step SHALL run.

WHEN the sync PR is missing, red or pending
THEN the brief answers `action=skip` with the reason, and the job spends no model call.

#### Scenario: a pending check is not a review
Given an open sync PR whose checks are one `pass` and one `pending`
When  the precondition is read
Then  the PR is found, it is not green, and the pending check is named in the reason.

- **Test:** `tests/test_registry_review.py::test_the_precondition_is_every_check_green_on_an_open_sync_pr`

#### Scenario: no open sync PR is a skip with a reason
Given no open `chore/registry-sync` pull request
When  the precondition is read
Then  `action=skip` is printed and the reason states what would have to exist instead.

- **Test:** `tests/test_registry_review.py::test_no_open_sync_pr_is_a_skip_with_a_reason` and
  `tests/test_registry_review.py::test_the_brief_says_skip_and_still_renders_the_check`

### Requirement: the selection names the fastest server that fits the card

The selection check SHALL, for every `(arch, vram, ram)` case the trend list is built from, list the
models `trend_list()` lists for that card and, per model, the server `rank_engines()` puts first with
its measured t/s. It SHALL report a `slower-than-class` finding when a faster engine of the SAME rank
class exists, `no-engine` when a listed model has no engine image, `unmeasured` when the named server
has no measured t/s, and `empty-tier` when a card lists nothing.

WHEN the list names a server that is not the fastest of its own rank class
THEN a `slower-than-class` finding names both engines and both figures.

#### Scenario: a correct list has no finding
Given a store whose two engines are proven on the same card class, the second faster
When  the selection check runs for that card size
Then  the row names the faster engine at its measured figure and there is no finding.

- **Test:** `tests/test_registry_review.py::test_the_selection_names_the_fastest_server_of_its_own_card_class`

#### Scenario: a slower server of the same class is a finding
Given the same store and an engine order that names the slower engine first
When  the selection check runs
Then  a `slower-than-class` finding states the named engine's t/s and the faster engine's t/s.

- **Test:** `tests/test_registry_review.py::test_a_list_that_names_a_slower_server_of_the_same_class_is_a_finding`

#### Scenario: an unserveable model and an empty tier are named, never silent
Given a listed model with no engine image for the arch, and a card size that lists nothing
When  the selection check runs
Then  a `no-engine` finding and an `empty-tier` finding are reported.

- **Test:** `tests/test_registry_review.py::test_a_listed_model_no_engine_can_run_is_a_finding` and
  `tests/test_registry_review.py::test_a_tier_that_lists_nothing_is_a_finding`

### Requirement: the review becomes ONE issue, labelled for the implementer

`make registry-review-publish` SHALL file exactly one issue labelled `agent:implement` from the leg's
`registry-review.md`, carrying a `<!-- registry-sync-review: <generated_utc> -->` marker. A run for a
store that already has such an issue SHALL edit it, never create a second one. A `VERDICT: clear`
verdict file SHALL file nothing and exit 0.

WHEN the store's review is published
THEN exactly one issue exists for that `generated_utc`, labelled `agent:implement`.

#### Scenario: the first publish creates exactly one labelled issue
Given a review body and no open issue carrying this store's marker
When  `make registry-review-publish` runs
Then  exactly one issue is created, labelled `agent:implement`.

- **Test:** `tests/test_registry_review.py::test_a_store_with_no_issue_yet_creates_exactly_one_labelled_issue`

#### Scenario: a second publish edits instead of duplicating
Given an open issue that already carries this store's review marker
When  the review is published again
Then  that issue is edited and nothing is created.

- **Test:** `tests/test_registry_review.py::test_a_second_publish_for_the_same_store_updates_instead_of_duplicating`

#### Scenario: the change report is linked, not repeated
Given an open change issue (#704) for the same store
When  the review is published
Then  the new body names that issue as the store's change report.

- **Test:** `tests/test_registry_review.py::test_the_review_names_the_store_change_report_instead_of_repeating_it`

#### Scenario: a clear verdict files nothing
Given a verdict of `clear` with a reason
When  `make registry-review-publish` runs
Then  it exits 0, reports the reason, and touches no issue.

- **Test:** `tests/test_registry_review.py::test_a_clear_verdict_files_nothing`

### Requirement: the workflow spends a model only behind the brief and calls only make targets

The `registry-sync-review` workflow SHALL gate every step that reads a secret or starts the agent on
`steps.brief.outputs.action == 'review'`, SHALL run only `make` targets (never `python3 scripts/…`
directly), and SHALL upload only the REDACTED transcript.

WHEN a run starts with no green sync PR
THEN the brief decides, every later step is skipped, and nothing is filed or published.

#### Scenario: the gating and the targets are in the workflow
Given the workflow text
When  the steps after the brief are read
Then  each one that runs a make target is gated on the brief's `review`, and no step calls a script
      directly.

- **Test:** `tests/test_registry_review.py::test_the_workflow_only_runs_the_review_behind_a_green_brief`

### Requirement: the leg runs under ONE project skill

The leg SHALL preload `.hermes/skills/registry-sync-review/SKILL.md`, whose frontmatter `name` matches
its directory and which carries `## Inputs`, `## Output` and `## Rules`.

WHEN the leg is inspected
THEN the skill it names exists, states its one output file, and `make check-agent-skills` passes.

#### Scenario: the skill is the leg's contract
Given the skill file the make leg preloads
When  its frontmatter and required sections are read
Then  the name matches the directory and Inputs/Output/Rules are present, naming `registry-review.md`.

- **Test:** `tests/test_registry_review.py::test_the_skill_is_the_legs_contract` and
  `make check-agent-skills`
