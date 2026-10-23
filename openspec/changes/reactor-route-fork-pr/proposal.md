# A failed fork-PR run is repaired, not filed as an issue

## Why

`run-failure-reactor` reacts to every completed CI run and routes a failure either to the fix-bot
(Route A) or to a new `agent:implement` issue (Route B). On this repository Route A is effectively dead:

- `_pr_from_run()` only reads the REST run object's `pull_requests`, which is **empty for a fork
  `pull_request` run** (measured, #277/#170) — and it explicitly refuses a fork head ("the token cannot
  push it"). Every agent PR is pushed to `andyholst/llgenie`, so every red agent-PR run fell to Route B:
  #507, #537 and #542 are all reactor-filed issues carrying `event: pull_request`.
- Even when it does dispatch, the dispatched run is refused: `dispatch_fix_bot()` shells `gh workflow run`
  with the step's `GH_TOKEN: ${{ github.token }}`, so the new run's actor is `github-actions[bot]` and
  fix-bot's guard refuses it — measured on run `39917926028`:
  `Refused: github-actions[bot] is not the owner or a collaborator with write access (permission: none)`.
- The capability exists and is unused: `fix_bot_sweep.eligible(..., own_fork=...)` already accepts the
  owner's fork (that is how the sweep repairs fork PRs, #477).

Filing an issue for a failure that is happening *on a PR already being worked on* is what keeps the
`agent:implement` backlog growing — the backlog the refiner cannot keep up with (#535, #547).

## What Changes

- **`scripts/run_failure_reactor.py`** — for a run whose REST `pull_requests` is empty, the PR is resolved
  from the run's `head_branch` + `head_repository.owner.login` with `scripts/resolve_run_pr.py` (the
  resolver auto-merge already uses), then passed through `fix_bot_sweep.eligible(..., own_fork=TRUSTED_FORK)`
  — no duplicated rules. The owner's fork is routed; a fifth-party fork is reported and left alone. The
  dispatch requires `DISPATCH_TOKEN` (owner identity) from the environment, uses it for `gh workflow run`
  only, and fails loudly when it is missing instead of producing a red no-op run.
- **`Makefile`** — `DISPATCH_TOKEN` defaults to `$(GH_TOKEN)` and is `export`ed, so the identity reaches
  the child process by environment only (never argv, never a log).
- **`.github/workflows/run-failure-reactor.yml`** — the step sets `DISPATCH_TOKEN: ${{ secrets.BUMP_TOKEN }}`.
- **`tests/test_run_failure_reactor.py`** — the real reactor against a real fake `gh`: a red fork-PR run
  dispatches and the dispatch carries the owner token; a missing token is loud and dispatches/files
  nothing; a fifth-party fork and a draft still fall back to the issue.

## Impact

- A red fork-PR run is repaired by the fix-bot instead of minting a new work item, so the implementer's
  queue stops being fed by failures that are already being worked on.
- The dispatch can no longer silently produce a red run that nobody notices.
