# rebase-sweep-reliability

## ADDED Requirements

### Requirement: the sweep issues only `gh`-valid argv

`rebased_today()` SHALL request only fields the real `gh` exposes, so the sweep does not die on a
rejected query. `gh search prs` carries no comment bodies, so the marker is read from each candidate
PR's comments via `gh pr view <n> --json comments`.

#### Scenario: the sweep does not ask `search prs` for comment bodies

- **GIVEN** the sweep runs against a `gh` that refuses `--json ...comments...` on `search prs` (as
  the real CLI does),
- **WHEN** it computes which PRs were rebased today,
- **THEN** it completes, and the only call that carries the comment bodies is
  `gh pr view <n> --json comments`.

- **Test:** `tests/test_rebase_bot_sweep.py::test_the_sweep_never_asks_search_prs_for_a_field_the_cli_lacks`

#### Scenario: a marker written today is found

- **GIVEN** an open PR whose comments carry this bot's marker for today,
- **WHEN** `rebased_today()` runs,
- **THEN** it returns that PR's number.

- **Test:** `tests/test_rebase_bot_sweep.py::test_a_marker_written_today_is_found`

#### Scenario: another day's marker is not today's record

- **GIVEN** a PR whose comments carry the marker for a different day,
- **WHEN** `rebased_today()` runs for today,
- **THEN** it returns nothing.

- **Test:** `tests/test_rebase_bot_sweep.py::test_a_marker_from_another_day_is_not_counted`

### Requirement: a failed sweep is loud, never a green no-op

The `rebase-bot.yml` sweep step SHALL fail the run when the sweep exits non-zero, so a crashed
decision cannot be mistaken for "nothing to do".

#### Scenario: a non-zero sweep fails the step

- **GIVEN** the sweep step's `run:` block,
- **WHEN** it is read,
- **THEN** it captures the sweep's exit code and exits non-zero when it is not 0.

- **Test:** `tests/test_rebase_bot_sweep.py::test_the_sweep_step_fails_loudly_when_the_sweep_fails`
