# bot-credential-scope

## ADDED Requirements

### Requirement: a job that calls an agent leg carries the keys that leg's guard demands

`make test-unit` MUST fail, naming the workflow, the job, the leg and the variable, when a step runs
`make <leg>` for an agent leg — a make target whose recipe starts `$(AGENT_IMAGE)` and whose recipe
begins with `python3 scripts/require_env.py <KEYS>` — and the workflow `env:`, the job `env:` or that
step's own `env:` does not declare a key the guard requires. A sibling step's `env:` MUST NOT satisfy
the rule (issue #364's shape). The roster MUST be derived from the Makefile and the workflow files, so
a workflow added after this change is covered without an edit to the rule.

WHEN a step runs a guarded agent leg and neither its job's env nor its own env declares a key that
leg's `require_env.py` line demands
THEN `make test-unit` exits non-zero and names the workflow, job, leg and missing variable.

#### Scenario: the dedupe sweep's preflight has no TypeSafe key

- **Given** the `dedup` job as `issue-dedupe.yml` shipped it at `main@464fee5` — `NOUS_API_KEY` on the
  job env, a step running `make agent-jev-preflight NERVE_REQUIRE=1`
- **When** the derived scope rule walks every workflow
- **Then** it reports `issue-dedupe.yml:dedup` running `make agent-jev-preflight` without
  `TYPESAFE_API_KEY`, the exact variable the run died on (`run 40702295009`, job `122867360526`)
- **Test:** `tests/test_agent_shell_keys.py::test_the_guard_scope_detector_catches_the_802_shape`

#### Scenario: the key on the job env or on that step's env satisfies the rule

- **Given** the same job with `TYPESAFE_API_KEY` declared on the job `env:`, and again with it on the
  preflight step's own `env:`
- **When** the scope rule reads each
- **Then** both pass, and a key on a SIBLING step still does not
- **Test:** `tests/test_agent_shell_keys.py::test_the_guard_scope_detector_catches_the_802_shape`

#### Scenario: every leg-calling workflow in the tree is covered

- **Given** the committed tree (14 guarded legs, 29 leg calls across 9 workflows at `main@464fee5`)
- **When** `make test-unit` runs the derived rule
- **Then** it inspects at least 20 leg calls and finds no job that withholds a key its leg's guard
  demands
- **Test:** `tests/test_agent_shell_keys.py::test_every_workflow_that_calls_an_agent_leg_sets_the_keys_its_guard_requires`

### Requirement: the two bot jobs that arm the JEV preflight receive its key

`issue-dedupe.yml`'s `dedup` job and `registry-sync-review.yml`'s `review` job MUST declare
`TYPESAFE_API_KEY: ${{ secrets.TYPESAFE_API_KEY }}` on the job env, because both run
`make agent-jev-preflight NERVE_REQUIRE=1`, whose first recipe line is
`scripts/require_env.py TYPESAFE_API_KEY`. A run of either workflow must not be able to die at that
guard for a missing key.

WHEN either job's preflight step runs with the repository secret available
THEN `scripts/require_env.py TYPESAFE_API_KEY` exits 0 and the preflight proceeds, instead of exiting 2
with `FATAL: TYPESAFE_API_KEY is missing or empty`.

#### Scenario: the guard's exit status is the one the run saw

- **Given** a process environment without `TYPESAFE_API_KEY`
- **When** `python3 scripts/require_env.py TYPESAFE_API_KEY` runs
- **Then** it exits 2 and names the variable (the measured failure of #802)
- **Test:** `tests/test_require_env.py::test_a_missing_key_exits_2_and_names_the_variable`

#### Scenario: both jobs now declare the key

- **Given** the two workflows after this change
- **When** the derived scope rule reads `dedup` and `review`
- **Then** neither is reported, because the job env declares `TYPESAFE_API_KEY`
- **Test:** `tests/test_agent_shell_keys.py::test_every_workflow_that_calls_an_agent_leg_sets_the_keys_its_guard_requires`
