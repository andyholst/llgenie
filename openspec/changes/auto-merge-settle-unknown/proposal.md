# Wait for `mergeable` instead of deferring on UNKNOWN

## Why

GitHub computes `mergeable` asynchronously, so a read immediately after a CI run finishes can answer `UNKNOWN` —
neither "conflicts" nor "mergeable". `run()` decided from that single read, `review_blocked()` was false (it
requires `MERGEABLE`), so the approve-then-merge path was never attempted and the gate deferred. Measured on PR
#552 (run 39931464102): `reason: mergeable is UNKNOWN (conflicts, or GitHub has not finished computing it)`, then
nothing retried it while the PR sat green and `mergeable: MERGEABLE`.

The retry sweep #546 added has also never run: `auto-merge.yml` is `active` and its file carries
`schedule: "*/30 * * * *"`, but the workflow has produced **zero `schedule` runs** (30 of 30 are `workflow_run`),
while `issue-refiner.yml`'s hourly cron runs fine in the same repository. A deferral therefore waits for a push
that may never come.

## What Changes

- **`settle_mergeable()`** in `scripts/auto_merge.py`: bounded polling (6 × 5 s by default) until `mergeable` is
  a settled value; `run()` calls it before deciding. A PR that settles to `MERGEABLE`/`CLEAN` merges through the
  normal path; one that never settles defers with a real reason.
- **The recheck job runs on every CI completion**: `needs: [merge]` + `if: always()`, so a deferral is retried by
  the trigger that demonstrably fires, with the 30-minute cron kept as a backstop.

## Impact

- A green PR on a transient `UNKNOWN` merges without a human re-run, and a deferral from any cause is retried on
  the next `CI` completion instead of waiting for a push.
