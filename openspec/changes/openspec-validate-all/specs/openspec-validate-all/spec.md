# openspec-validate-all

## ADDED Requirements

### Requirement: the openspec gate validates every active change

`make openspec-validate-all` MUST validate the structure of every ACTIVE change under
`openspec/changes/`, and `ci-openspec` MUST run it. No CI gate may validate a single hardcoded change
name.

WHEN a commit introduces an OpenSpec change
THEN the openspec job validates that change along with every other active one.

#### Scenario: the CI job validates all changes

- **Given** `ci-openspec` in the Makefile
- **When** its recipe is read
- **Then** it runs `openspec-validate-all` (not `openspec-validate NAME=<one>`)
- **Test:** `tests/test_openspec_gate.py::test_ci_validates_every_active_change`

#### Scenario: the loop validates all changes unless asked for one

- **Given** `scripts/loop_harness.py`
- **When** its openspec stage is read
- **Then** without `NAME` it runs `make openspec-validate-all`, and with `NAME` it runs that one
- **Test:** `tests/test_openspec_gate.py::test_the_loop_validates_all_changes_without_a_name`
