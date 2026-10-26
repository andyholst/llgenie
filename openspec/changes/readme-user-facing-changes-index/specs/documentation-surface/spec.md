# documentation-surface

## ADDED Requirements

### Requirement: the README is the user guide, and its history lives elsewhere

`README.md` MUST describe what llgenie is, how to install it, how to use it and how it works, and
MUST link the references that hold the rest: `docs/ARCHITECTURE.md` (the code map),
`docs/ENGINES.md` (engine build/serve), `docs/BOTS.md` (automation) and `CHANGES.md` (the change
index). It MUST NOT carry a section whose heading names an issue, a change-log heading, or the
generated dispatch table — a change is never documented by appending to the README.

WHEN a change is appended to `README.md` as an `(issue #N)` section
THEN `make check-docs` fails, naming the heading and where the change belongs.

#### Scenario: the real README is a guide with no change history

- **Given** the real checkout and its documentation surface
- **When** the documentation is checked
- **Then** there is no issue-numbered change heading, no change-log heading and no dispatch marker in `README.md`
- **And** `README.md` links `CHANGES.md`, `docs/ARCHITECTURE.md`, `docs/ENGINES.md` and `docs/BOTS.md`
- **Test:** `tests/test_check_docs.py::test_the_real_tree_documents_every_user_facing_target`

#### Scenario: an appended change section fails, a change-log heading fails, the dispatch marker fails

- **Given** a README whose heading is `## Installation is isolated (issue #275)`
- **When** the documentation is checked
- **Then** it fails, saying that heading is change history and the change belongs in `agent-wiki/`
- **And** a `## Changelog` heading and a `<!-- dispatch-forms:begin -->` block fail the same way
- **Test:** `tests/test_check_docs.py::test_the_readme_carries_no_change_history`

### Requirement: every change has one dated note, indexed in CHANGES.md

Every `agent-wiki/YYYY-MM-DD-<kebab>.md` note MUST reference the issue or PR it implements, and
MUST be linked from `CHANGES.md`. Every row in `CHANGES.md` MUST point at a note that exists.
`README.md` MUST link `CHANGES.md`, so a reader can reach the history.

WHEN a change lands without its `CHANGES.md` row
THEN `make check-docs` fails, naming the note that is not indexed.

#### Scenario: an unindexed note fails and its row is the fix

- **Given** a real note in `agent-wiki/` that `CHANGES.md` does not link
- **When** the documentation is checked
- **Then** it fails, naming the note as not indexed
- **And** adding its row makes the check pass
- **Test:** `tests/test_check_docs.py::test_a_note_missing_from_the_index_fails_and_its_row_fixes_it`

#### Scenario: the index cannot invent history

- **Given** a `CHANGES.md` row linking a note that is not on disk
- **When** the documentation is checked
- **Then** it fails, naming the row's note as missing
- **And** a README with no link to `CHANGES.md` fails too
- **Test:** `tests/test_check_docs.py::test_an_index_row_pointing_at_a_missing_note_fails`

### Requirement: a target is documented in the doc that fits it

A make target carrying a `##` help line MUST be named whole-token in `README.md` or in a markdown
file under `docs/` that `README.md` links. A user target belongs in the README; an automation
target belongs in `docs/BOTS.md`. A target documented nowhere MUST be a recorded, dated decision in
`tests/fixtures/docs-exceptions.json`, and a decision that is no longer needed MUST be reported stale.

WHEN an automation target is documented only in a `docs/` page the README does not link
THEN `make check-docs` fails, naming the target.

#### Scenario: a docs page reaches a target, an unlinked page does not

- **Given** a README linking `docs/BOTS.md` and a target named only there
- **When** the documentation is checked
- **Then** the run is clean
- **And** removing the link makes the same target undocumented and the check fails
- **Test:** `tests/test_check_docs.py::test_an_automation_target_is_documented_in_a_docs_page_the_readme_links`

## MODIFIED Requirements

### Requirement: no bot writes the README

The dispatch table is generated into `docs/BOTS.md`, verified there by
`scripts/check_dispatch_forms.py`; the engine bump rewrites `tests/` and `docs/` only. A producer
that writes `README.md` is a defect.

WHEN the dispatch table is stale
THEN `make check-dispatch-forms` fails, naming `docs/BOTS.md` — never the README.

#### Scenario: the dispatch table's home is docs/BOTS.md

- **Given** the real workflows and `docs/BOTS.md`
- **When** `check_dispatch_forms.py check` runs
- **Then** the table there matches the workflows, and no table is required in `README.md`
- **Test:** `tests/test_dispatch_forms.py::test_a_stale_dispatch_table_fails_and_a_fresh_one_passes`

#### Scenario: an engine bump never rewrites the README

- **Given** a checkout whose pinned-version facts live in `docs/ENGINES.md` and `tests/`
- **When** a real bump moves the pin
- **Then** the docs and the pin asserts are rewritten, and `README.md` is unchanged
- **Test:** `tests/test_engine_bump.py::test_bump_rewrites_hardcoded_pin_asserts`
