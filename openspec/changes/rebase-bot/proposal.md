# Keep every open PR on `main`, one PR at a time

## Why

A PR behind `main` cannot be merged (AGENTS.md), so a stale PR blocks itself until a human
rebases it. Only `chore/engine-bump-*` PRs were handled, and only when the merge applied cleanly;
a conflict was left for a human. Every other PR drifted.

## What changes

- A 6-hourly bot with a decision in code (`scripts/rebase_bot_sweep.py`): ONE open, non-draft PR
  against `main` per run, oldest first, whose state is `BEHIND` or `DIRTY`, with a reason for every
  pass-over, skipping a PR already rebased **today** (its marker comment) and any fork it cannot
  push to.
- `scripts/rebase_bot.sh` does it: `rerere` off, a conflict handed to the agent with the hard rules
  (preserve both sides, never weaken a test, keep the recipe TAB), the result verified structurally
  (`make -n ci-unit`, `make lint`, `make check-wiring`), then pushed **`--force-with-lease` to the
  PR's own head remote** — a fork PR goes to the fork. Nothing is merged, and an unfinished
  resolution is reported on the PR.
- `rebase-bot.yml`: schedule + manual dispatch, one job that always runs (#107), owner-guarded,
  the agent inside the agent image.

## Impact

Open PRs stop rotting behind `main`, and the one class that used to need a human — a conflicting
rebase — is resolved and verified mechanically. The daily cap (5) and the once-a-day marker bound
the work, so a PR cannot be rebased in a loop.
