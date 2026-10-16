# The rebase bot's sweep must run, and its failure must be loud (issue #309)

**Issue:** [#309](https://github.com/asimov-agent/llgenie/issues/309)
**Capability:** `rebase-sweep-reliability`

## Why

The rebase bot has never rebased a single PR, and every run reports SUCCESS.

`scripts/rebase_bot_sweep.py` asks `gh` for a field that does not exist:

```
$ make rebase-bot-sweep REPO=asimov-agent/llgenie OWN_FORK=andyholst
[rebase-bot] gh search prs --repo asimov-agent/llgenie --commenter github-actions[bot] --updated >=2026-10-16 --json number,comments --limit 50 failed (1): Unknown JSON field: "comments"
```

`gh search prs` has no `comments` field (the bodies); the real field is `commentsCount`. The same
crash is in every scheduled run (e.g. [38810528684](https://github.com/asimov-agent/llgenie/actions/runs/38810528684)).

It was invisible because `rebase-bot.yml`'s sweep step runs under `set +e`, captures nothing, and
writes `action=unknown` → `go=false` → the rebase step is skipped and the run is green. **A crashed
decision and "nothing to do" are indistinguishable in the log**, so the bot sat dead behind a green
pipeline.

A second, independent bug is in the same function: `--commenter github-actions[bot]` is the wrong
author (the bot comments with the owner PAT), so even with a valid field the "already rebased today"
record would always be empty:

```
$ gh search prs --repo asimov-agent/llgenie --commenter "github-actions[bot]" --updated ">=2026-10-15" --json number --limit 5
[]
```

The daily cap would never apply and a PR could be rebased in a loop.

## What Changes

- **`scripts/rebase_bot_sweep.py`** — `rebased_today()` uses only `gh`-valid argv: it finds candidate
  PRs with `gh search prs --json number`, then reads each one's marker from
  `gh pr view <n> --json comments` (the call `_comments()` already uses and the only one that
  carries the bodies). The `--commenter` filter is dropped: the marker itself identifies the bot's
  record, so no author guess is needed.
- **`.github/workflows/rebase-bot.yml`** — the sweep step captures the sweep's exit code and FAILS
  LOUDLY on non-zero, instead of reporting `action=unknown` and a green run.
- **`tests/test_rebase_bot_sweep.py`** — the fake `gh` now REFUSES `--json ...comments...` on
  `search prs`, exactly as the real CLI does, so the pre-fix sweep fails the suite; new tests pin
  `rebased_today()`'s behaviour (today's marker found, another day's ignored) and the workflow's
  loud-failure guard.

## Impact

The rebase bot starts actually picking a PR (it was a no-op). A future crash in the sweep turns the
run red instead of silently skipping the work.

## Not covered

- The same `set +e` swallow in the sibling bot workflows (`issue-bot`, `fix-bot`, `issue-refiner`,
  `engine-bump-rebase`) — filed separately; each bot's own change owns its decision step.
- The `engine-bump-rebase.yml` "workflow file issue" push runs — a separate anomaly, its own issue.
