# 2026-10-15 — issue #309: the rebase bot's sweep runs again, and its failure is loud

Part of the "exercise every bot dispatcher one at a time" sweep. Exercising `rebase-bot.yml` showed
the bot had **never rebased a PR**, while every run reported SUCCESS.

## What was done

- OpenSpec change `rebase-sweep-valid` created FIRST via the containerized CLI (`make openspec-new`),
  validated, all tasks ticked.
- `scripts/rebase_bot_sweep.py`: `rebased_today()` no longer asks `gh search prs` for `comments`
  (not a field the CLI has — only `commentsCount`), which was a hard error killing the sweep on every
  run. It now finds candidates with `gh search prs --json number` and reads the marker from each PR's
  comments via `_comments()` (`gh pr view <n> --json comments`). The `--commenter github-actions[bot]`
  filter is dropped — the bot comments as the owner PAT, so it returned `[]`.
- `.github/workflows/rebase-bot.yml`: the sweep step captures the sweep's exit code and exits 1 on a
  non-zero one, so a crashed decision is never again reported as `action=unknown` + a green no-op.
- `tests/test_rebase_bot_sweep.py`: the fake `gh` now REFUSES `--json ...comments...` on
  `search prs` exactly as the real CLI does; the marker fixtures moved from the search row to
  `comments_by_pr` (the real two-call shape); four new tests pin the argv, the today/other-day
  marker behaviour, and the workflow's loud-failure guard.

## Verified

- `tests/test_rebase_bot_sweep.py` in `llgenie/test:latest` (`:ro`): **19 passed**.
- Rule 6c: the 4 new tests FAIL on the pre-fix tree (`4 failed, 15 deselected`) and pass after.
- Live: `make rebase-bot-sweep REPO=asimov-agent/llgenie OWN_FORK=andyholst` now RUNS
  (`pass-over: #170 is UNKNOWN`, `#308 is BLOCKED`, `action=none`) where it previously crashed.
- `make lint`, `make openspec-validate NAME=rebase-sweep-valid`, `make check-wiring`, `make check-docs`
  green.

## Status

- Branch `fix/rebase-sweep-valid`, PR [#310](https://github.com/asimov-agent/llgenie/pull/310)
  against `asimov-agent/llgenie:main`, `closes #309`.
- Not covered (separate): the same `set +e` swallow in the sibling bot workflows, and the
  `engine-bump-rebase.yml` "workflow file issue" push runs.
