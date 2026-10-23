# 2026-10-23 — wait for `mergeable` instead of deferring on UNKNOWN (#558)

**Issue:** [#558](https://github.com/asimov-agent/llgenie/issues/558) · **PR:** the PR that closes it

## What was wrong

PR #552 was green (26 checks, `mergeable: MERGEABLE`, only a review missing) and stayed open. Its gate ran once
and deferred at 09:23Z with `mergeable is UNKNOWN (conflicts, or GitHub has not finished computing it)`: GitHub
computes `mergeable` asynchronously, `review_blocked()` requires `MERGEABLE`, so the approve-then-merge path was
never attempted. Nothing retried it — and the retry sweep added in #546 has **never run**: `auto-merge.yml` has
zero `schedule` runs (30 of 30 `workflow_run`) while `issue-refiner.yml`'s cron runs fine in the same repo.

## What changed

- `settle_mergeable()` polls a bounded 6 × 5 s until `mergeable` is settled; `run()` calls it before deciding, so
  a transient `UNKNOWN` becomes a merge instead of a deferral, and a state that never settles still defers with a
  real reason.
- The `recheck` job now runs on **every CI completion** (`needs: [merge]`, `if: always()`) with the cron kept as a
  backstop, so any deferral is retried by the trigger that actually fires.

## Verified

- `pytest tests/test_auto_merge.py tests/test_dispatch_forms.py tests/test_workflow_guards.py` →
  **88 passed**, including a PR whose first two reads are `UNKNOWN` then merges without `--admin`, and the
  bounded give-up.
- `make lint`, `make check-workflows`, `make check-docs`, `make openspec-validate NAME=auto-merge-settle-unknown`,
  `make openspec-tasks-check` green; `make test-unit` runs in the PR's checks.

## Note

PR #552 itself merged at 09:39:26Z (`mergedBy=asimov-agent`) once a run happened to read a settled state — the
fix removes the dependency on luck.
