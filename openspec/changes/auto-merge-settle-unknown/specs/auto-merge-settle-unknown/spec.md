# auto-merge-settle-unknown

## ADDED Requirements

### Requirement: An UNKNOWN mergeable is waited for, not treated as a verdict

When `mergeable` answers `UNKNOWN`, the gate SHALL re-read the PR a bounded number of times until GitHub settles
it, and SHALL then decide from the settled state. A PR that settles to `MERGEABLE` + `CLEAN` SHALL merge through
the normal path, never through `--admin`.

WHEN the first read of a green PR answers `mergeable: UNKNOWN`
THEN the gate waits and merges once the state settles.

#### Scenario: an unknown state settles into a merge

Given a green PR whose first two reads answer `mergeable: UNKNOWN` and whose third answers `MERGEABLE` + `CLEAN`
When  the gate runs
Then  it reads at least three times and merges without `--admin`.

- **Test:** `tests/test_auto_merge.py::test_an_unknown_mergeable_is_waited_for_not_deferred`

#### Scenario: a state that never settles still defers

Given a PR that answers `UNKNOWN` forever
When  the settle helper runs with two attempts
Then  it returns the last read and spends exactly two `pr view` calls, so the caller defers with a real reason.

- **Test:** `tests/test_auto_merge.py::test_settle_mergeable_gives_up_after_its_attempts`

### Requirement: The retry sweep runs on every CI completion

The `recheck` job SHALL run after the `merge` job on every `CI` completion (`needs: [merge]`, `if: always()`),
in addition to the 30-minute cron, because the cron has never fired for this workflow in this repository.

WHEN a `CI` run completes
THEN the recheck sweep runs and re-evaluates the PRs deferred at their current head.

#### Scenario: the recheck is wired to CI completions

Given `.github/workflows/auto-merge.yml`
When  the recheck job is read
Then  it declares `needs: [merge]` and `always()`, and the cron trigger is still declared.

- **Test:** `tests/test_auto_merge.py::test_the_recheck_runs_on_every_ci_completion_too`
