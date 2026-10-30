# documentation-surface

## MODIFIED Requirements

### Requirement: CHANGES.md is rendered from the fragments, never hand-merged

`CHANGES.md` MUST be rendered from `docs/changes.d/` by `make changes-index`
(`scripts/changes_index.py`), newest first and deterministic, and it MUST keep being committed and
linked from `README.md`. A change PR MUST NOT edit it; the documentation lane refreshes it, and
`make changes-index-report` states how far behind it is.

The gate therefore MUST NOT require the committed table to be current. It MUST require only
**membership**: every `agent-wiki/` note has exactly one fragment, every fragment indexes a note
that exists, and every row the committed table carries is a row the renderer would write — a stale
index may lag the fragments, it may never disagree with them.

WHEN a change adds its note and its `docs/changes.d/` fragment and does not touch `CHANGES.md`
THEN `make check-docs` is green, and `make changes-index-report` says the index is `N row(s) behind`.

#### Scenario: a fragment-only change is green through the library and through the CLI

Given a checkout whose `agent-wiki/` note and `docs/changes.d/` fragment were added and whose committed `CHANGES.md` was not touched,
When   the documentation is checked through `check_docs.problems()` and through `scripts/check_docs.py check`,
Then   both are green and the two answer the same question.
- **Test:** `tests/test_check_docs.py::test_a_fragment_only_change_is_green_and_the_index_may_lag_the_fragments`

#### Scenario: the committed table is the renderer's output, or is reported behind it

Given the real checkout,
When   the fragments are rendered, checked and reported,
Then   every fragment parses, every note has exactly one row, and `CHANGES.md` is accepted whether it already carries every row or reads `N row(s) behind`.
- **Test:** `tests/test_changes_index.py::test_the_real_index_accepts_a_committed_changes_md_that_lags_the_fragments`

#### Scenario: a row the renderer would never write is still a defect

Given the real checkout,
When   the rows committed in `CHANGES.md` are compared with the rendered table,
Then   each committed row is one the renderer writes, and a row linking a note that does not exist fails `make check-docs`.
- **Test:** `tests/test_changes_index.py::test_the_real_index_accepts_a_committed_changes_md_that_lags_the_fragments`

#### Scenario: the renderer is the only author of the table

Given a scratch checkout with two notes and two fragments whose committed `CHANGES.md` carries neither row,
When   `changes_index.py write` runs twice,
Then   `check` is green both before and after (a lag is not a defect), the first run writes exactly the rendered table, and the second run changes nothing.
- **Test:** `tests/test_changes_index.py::test_write_renders_a_lagging_index_and_is_idempotent`

#### Scenario: an index row that links a missing note is red in both

Given a checkout whose committed `CHANGES.md` carries a row for an `agent-wiki/` note nobody wrote,
When   the documentation is checked through the library and through the CLI,
Then   both fail and name the note that does not exist.
- **Test:** `tests/test_check_docs.py::test_a_fragment_only_change_is_green_and_the_index_may_lag_the_fragments`

#### Scenario: the gate still fails when the README cannot reach the index

Given a README with no link to `CHANGES.md`,
When   `make check-docs` runs,
Then   it fails saying the README does not link the index.
- **Test:** `tests/test_check_docs.py::test_the_readme_must_link_the_change_index`
