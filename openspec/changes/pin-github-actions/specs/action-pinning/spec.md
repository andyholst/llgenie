## ADDED Requirements

### Requirement: Every third-party action runs at a commit

Every `uses:` reference in `.github/workflows/**` and `.github/actions/**` that names a
third-party action MUST carry a full 40-character commit SHA. A tag, a branch, a short SHA or a
missing ref MUST fail the gate.

A reference to this repository's own content (`./.github/actions/…`, `./.github/workflows/…`) and
a `uses:` value that is not an action ref (a matrix value) are exempt: they cannot move
independently of the commit being run, or they name no action.

#### Scenario: a floating tag fails the gate

Given a workflow whose step is `uses: actions/checkout@v4`,
When   `make check-actions` runs,
Then   it exits non-zero and names the file, the line and the ref.

- **Test:** `tests/test_pin_actions.py::test_floating_tag_fails_the_gate`

#### Scenario: a full commit SHA passes the gate

Given a workflow whose step is `uses: actions/checkout@<40-hex> # v4`,
When   `make check-actions` runs,
Then   it exits 0.

- **Test:** `tests/test_pin_actions.py::test_full_sha_passes_the_gate`

#### Scenario: an abbreviated SHA is not a pin

Given a workflow whose step is `uses: actions/checkout@11d5960`,
When   `make check-actions` runs,
Then   it exits non-zero, because a short SHA is still resolved by GitHub and can collide.

- **Test:** `tests/test_pin_actions.py::test_short_sha_fails_the_gate`

#### Scenario: local actions and reusable workflows are exempt

Given a workflow that uses `./.github/actions/docker` and `./.github/workflows/pipeline.yml`,
When   `make check-actions` runs,
Then   it exits 0, because this repository's own content cannot move independently.

- **Test:** `tests/test_pin_actions.py::test_local_action_and_reusable_workflow_are_exempt`

#### Scenario: a non-action uses value is not judged

Given a step whose `uses:` resolves to a matrix value rather than `owner/repo@ref`,
When   `make check-actions` runs,
Then   it exits 0 — the gate refuses refs it can judge, never text it cannot.

- **Test:** `tests/test_pin_actions.py::test_non_action_uses_value_is_not_judged`

### Requirement: The pin is readable and updatable

A pinned reference MUST keep its tag as a trailing comment, and `make update-actions` MUST
re-resolve every pinned tag to its current commit. Re-running it over an already-current tree
MUST leave the files byte-identical.

#### Scenario: update rewrites the ref and keeps the tag

Given a tree with `uses: actions/checkout@v4`,
When   `make update-actions` runs,
Then   the line becomes `uses: actions/checkout@<40-hex> # v4` and the gate passes.

- **Test:** `tests/test_pin_actions.py::test_update_pins_and_keeps_the_tag_readable`

#### Scenario: a second update is a no-op

Given a tree that is already pinned,
When   `make update-actions` runs again,
Then   every file is byte-identical to before the run.

- **Test:** `tests/test_pin_actions.py::test_update_is_idempotent`

### Requirement: This repository obeys its own gate

The tree that ships the gate MUST contain no floating third-party action ref.

#### Scenario: the real tree is fully pinned

Given this repository,
When   every `uses:` ref is read,
Then   no action-like ref is unpinned.

- **Test:** `tests/test_pin_actions.py::test_this_repository_is_fully_pinned`
