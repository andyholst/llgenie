# install-ci-claim

## ADDED Requirements

### Requirement: a help line's CI claim must match what CI does

A target's `##` help line MUST NOT claim CI coverage no CI job delivers, and a recorded exception
exists ONLY while that claim does.

WHEN a target's help line stops claiming CI coverage
THEN its recorded decision is stale and the wiring gate says to delete it.

#### Scenario: the local acceptance target stops claiming CI

- **Given** `make test-install-ci`, run by no CI job
- **When** its `##` help line is read
- **Then** it describes the local acceptance and names the `make ci-install` stages that cover the flow in CI
- **Test:** `tests/test_wiring.py::test_a_target_whose_help_line_claims_ci_coverage_is_guarded`

#### Scenario: a decision outlives its claim

- **Given** a target that no longer claims CI coverage and a dated decision recorded for it
- **When** the wiring gate runs
- **Then** it fails with "no longer claims CI coverage … the entry is stale — delete it"
- **Test:** `tests/test_wiring.py::test_a_decision_for_a_target_that_no_longer_claims_ci_is_stale`
