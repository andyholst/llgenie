# worktree-report

## ADDED Requirements

### Requirement: the report measures every worktree and mutates nothing

`make worktree-report` MUST NOT delete, move or unregister anything. For every entry of
`git worktree list --porcelain` it MUST print the path, the branch (`detached` when the entry holds
no branch), `merged-into-main` (yes/no, decided by a real `git merge-base --is-ancestor <head>
<base>`), `open-pr` (yes/no, decided by a real `gh pr list`) and `dirty` (yes/no, decided by
`git status --porcelain` inside that directory), and it MUST finish with a summary line that counts
the total, the merged-and-pr-less entries, the off-main-and-pr-less entries and the dirty entries.
It MUST exit 0 even when nothing is stale, and MUST exit non-zero naming the step when a measurement
fails, because an unreadable state is not a clean state.

WHEN a bot runs `make worktree-report` on a checkout that holds worktrees
THEN it prints one row per worktree with the four measured facts, plus a summary, and the worktree
set and branch set on disk are byte-identical afterwards.

#### Scenario: every worktree is reported with its four measured facts

- **Given** a repository with a main checkout, a worktree on a branch whose tip is an ancestor of the base, and a worktree on a branch that is not
- **And** an open PR for the second branch and an uncommitted change in its tree
- **When** the report runs
- **Then** each worktree has a row naming its path, branch, `merged-into-main`, `open-pr` and `dirty`, and the values match the repository's real state
- **Test:** `tests/test_worktree_report.py::test_report_lists_every_worktree_with_its_four_measured_facts`

#### Scenario: the report is byte-identical in, byte-identical out

- **Given** a repository with worktrees, one of them dirty and one on a branch with no PR
- **When** the report runs
- **Then** `git worktree list --porcelain` and `git branch --format=%(refname:short)` are byte-identical before and after
- **Test:** `tests/test_worktree_report.py::test_report_mutates_nothing`

#### Scenario: nothing stale still exits zero

- **Given** a repository whose only worktree is the main checkout on the base ref with no open PRs
- **When** the report runs
- **Then** it exits 0 and its summary says 1 worktree and 0 stale
- **Test:** `tests/test_worktree_report.py::test_report_of_a_clean_checkout_exits_zero`

#### Scenario: a failing gh lookup is loud

- **Given** a `gh` on `PATH` that exits non-zero
- **When** the report runs
- **Then** it exits non-zero and its message names the failing lookup instead of reporting `open-pr: no`
- **Test:** `tests/test_worktree_report.py::test_a_failing_gh_lookup_exits_non_zero`

### Requirement: a bot cannot run the destructive target without saying so

`make worktree-prune` MUST run a guard before `scripts/worktree_prune.py`. When `CI` or `BOT` is set
in the environment and `CONFIRM=1` is not given, the guard MUST exit non-zero with a message naming
`make worktree-report` and the `CONFIRM=1` re-run spelling, and the prune MUST NOT run. When neither
`CI` nor `BOT` is set, the guard MUST be a no-op so the owner's cleanup path is unchanged, and
`CONFIRM=1` MUST let a bot run the prune exactly as today.

WHEN a bot leg asks for `make worktree-prune` without `CONFIRM=1`
THEN the guard refuses, names the report target, and deletes nothing.

#### Scenario: a bot run without CONFIRM is refused

- **Given** `BOT=1` in the environment and no `CONFIRM`
- **When** the guard runs
- **Then** it exits non-zero and its message names `make worktree-report` and `CONFIRM=1`
- **Test:** `tests/test_worktree_report.py::test_the_guard_refuses_a_bot_run_without_confirm`

#### Scenario: a CI run without CONFIRM is refused

- **Given** `CI=true` in the environment and no `CONFIRM`
- **When** the guard runs
- **Then** it exits non-zero and deletes nothing
- **Test:** `tests/test_worktree_report.py::test_the_guard_refuses_a_ci_run_without_confirm`

#### Scenario: the owner's own cleanup is unchanged

- **Given** neither `CI` nor `BOT` in the environment and no `CONFIRM`
- **When** the guard runs
- **Then** it exits 0, so `make worktree-prune` behaves exactly as it did before this change
- **Test:** `tests/test_worktree_report.py::test_the_guard_is_a_no_op_for_the_owner`

#### Scenario: an explicit CONFIRM lets a bot prune

- **Given** `BOT=1` and `CONFIRM=1`
- **When** the guard runs
- **Then** it exits 0 and the prune proceeds
- **Test:** `tests/test_worktree_report.py::test_the_guard_allows_a_bot_with_confirm`

#### Scenario: the guard is wired ahead of the prune script

- **Given** the `Makefile`
- **When** the `worktree-prune` recipe is read
- **Then** `scripts/worktree_prune_guard.py` runs before `scripts/worktree_prune.py`, and both `worktree-report` and `worktree-prune` carry a `##` help line and are declared `.PHONY`
- **Test:** `tests/test_worktree_report.py::test_the_makefile_wires_the_report_and_guards_the_prune`

### Requirement: no bot contract instructs an unattended agent to prune

The preloaded bot skills MUST NOT tell an unattended agent to run the destructive targets. Each
Rules section MUST say the bot reports with `make worktree-report` and leaves deletion to the owner,
naming `make worktree-prune`, `git worktree prune` and `git worktree remove` as the commands a bot
never runs unless the owner explicitly says so. (`AGENTS.md:483` carries the same defect and the same
replacement text; because this session's write gate refuses edits to a protected agent-instruction
file with no user present, that edit is recorded as OWED in the PR body, exactly as criterion 4
allows, and is not asserted by a test that cannot be satisfied.)

WHEN a bot leg preloads `bot-unattended` and its own skill
THEN it finds the report-and-leave-deletion rule and the three prohibited commands, and no
instruction to prune a branch or a worktree.

#### Scenario: both bot skills carry the prohibition

- **Given** `.hermes/skills/bot-unattended/SKILL.md` and `.hermes/skills/issue-implement/SKILL.md`
- **When** their Rules sections are read
- **Then** each names `make worktree-prune`, `git worktree prune` and `git worktree remove` as forbidden for a bot
- **And** each names `make worktree-report` as the reporting command
- **Test:** `tests/test_worktree_report.py::test_both_bot_skills_carry_the_prohibition`
