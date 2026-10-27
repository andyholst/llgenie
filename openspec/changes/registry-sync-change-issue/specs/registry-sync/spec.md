# registry-sync-change-issue

## ADDED Requirements

### Requirement: a changed store is stated as ONE issue

`make sync-change-issue` SHALL open exactly one issue — `sync: review the <generated_utc> trending
registry`, labelled `agent:implement` — whose body states what changed between the committed registry and
the working tree's: `generated_utc`, model and engine counts, added / removed / renamed model ids, engines
new to the registry, the `formats` vocabulary, every contract change, the README row changes, and the
derived-table counts. A run for a store version that already has an open issue SHALL update that issue and
SHALL NOT create a second one.

WHEN a sync produces a store whose `generated_utc` is not the committed one
THEN one issue exists that names the change, and a second run edits it.

#### Scenario: the first run for a store version files one issue

Given a synced store whose `generated_utc` differs from `HEAD`'s and no open issue carrying its marker
When  `make sync-change-issue` runs
Then  exactly one issue is created, labelled `agent:implement`, and its body names the store change.

- **Test:** `tests/test_registry_change_issue.py::test_a_store_with_no_open_issue_creates_exactly_one`

#### Scenario: a second run updates instead of duplicating

Given an open issue whose body carries the marker for that store's `generated_utc`
When  `make sync-change-issue` runs again
Then  that issue is edited and no new issue is created.

- **Test:** `tests/test_registry_change_issue.py::test_a_second_open_for_the_same_store_updates_instead_of_duplicating`

#### Scenario: a dry run touches nothing

Given `DRY=1`
When  `make sync-change-issue` runs
Then  it prints what it would do and neither creates nor edits an issue.

- **Test:** `tests/test_registry_change_issue.py::test_dry_run_mutates_nothing`

### Requirement: the report names every class of change llgenie must follow

The rendered body SHALL name a model added to the store, an engine new to the registry, a contract
`required` key added per model row, a new `backend` enum value, and the README rows that changed — and
SHALL state the work each implies, naming the issue that owns it (#693/#677, #673/#686, #694, #687/#692).

WHEN the store, contract and README all changed
THEN the body lists one entry per class and the work it implies.

#### Scenario: the three facts an agent needs are in the body

Given a previous store and a synced one that adds a model, adds an engine and adds a required contract key
When  the change report is rendered
Then  the body names the added model, the new engine and the added key, and says what to do about each.

- **Test:** `tests/test_registry_change_issue.py::test_the_report_names_an_added_model_a_new_engine_and_an_added_contract_key`

### Requirement: the analysis runs even when a gate is red

The `registry-sync` workflow SHALL run `make sync-change-issue` with `if: always()` on a changed store, so
the issue exists whether or not the job's gates passed.

WHEN the job's check step fails on a changed store
THEN the change-issue step still runs and files or updates the issue.

#### Scenario: the issue is filed on a red check step

Given a changed store whose check step failed
When  the `registry-sync` job evaluates the change-issue step
Then  it runs it (`always()`), so the issue exists with the store that could not land.

- **Test:** `tests/test_registry_change_issue.py::test_the_workflow_runs_the_step_even_when_a_gate_is_red`
