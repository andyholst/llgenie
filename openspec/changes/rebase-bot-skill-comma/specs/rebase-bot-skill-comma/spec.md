# rebase-bot-skill-comma

## ADDED Requirements

### Requirement: an agent leg's expanded command must be shell-safe

Every target whose recipe calls `$(call scrubbed_run,…)` MUST expand, under `make -n`, to a command
with balanced quoting. In particular, no `$(call …)` argument may contain a literal comma, because
make splits arguments before expansion and silently drops the remainder.

WHEN a leg's recipe is expanded
THEN the resulting shell command is complete: balanced single quotes and an intact skill list.

#### Scenario: a literal comma truncates the command

- **Given** a leg whose `$(call scrubbed_run,…)` body contains `-s a,b`
- **When** `make -n <leg>` expands it
- **Then** everything after `-s a` is gone and one single quote is unclosed
- **Test:** `tests/test_agent_legs_quoting.py::test_the_skills_come_from_a_variable_not_a_literal_comma` (the defect is pinned as absent) with `::test_every_scrubbed_leg_expands_to_balanced_quotes` (fails on the pre-fix Makefile: 3 failed, measured)

#### Scenario: rebase-bot keeps both skills

- **Given** `rebase-bot-agent`, the one leg that inlines its `hermes` command
- **When** the expanded recipe is read
- **Then** it carries `-s rebase-conflict,bot-unattended` from `$(REBASE_BOT_SKILLS)`
- **Test:** `tests/test_agent_legs_quoting.py::test_rebase_bot_keeps_both_of_its_skills`

### Requirement: the guard covers every scrubbed leg, not the one that broke

The regression test MUST derive its target list from the Makefile (every recipe that calls
`$(call scrubbed_run,…)`), so a leg added later is covered without editing the test.

WHEN a new scrubbed leg is added
THEN it is checked by the same test with no test change.

#### Scenario: the roster is derived

- **Given** the Makefile
- **When** the test collects targets whose recipe calls `scrubbed_run`
- **Then** it asserts on all of them, and the list is non-empty
- **Test:** `tests/test_agent_legs_quoting.py::test_every_scrubbed_leg_expands_to_balanced_quotes`
