# ci-path-scope — 2026-10-28

## What changed

- **`scripts/ci_scope.py`**: nine change classes, ten wildcard paths that select every class, and the job
  table of `ci.yml` as it is today (15 jobs, Linux-only, after #871 deleted the macOS group). Unmatched
  path → exit 1 naming it. CLI: `--paths`, `--base`, `--before`, `--all`, `--github-output`.
- **`ci.yml`**: `pull_request.paths-ignore` = `DOCS_TRIGGER_IGNORE` (the `docs` class minus its wildcards,
  with `AGENTS.md` re-included because it is a `*.md`); `push` unfiltered.
- **`.github/workflows/scope.yml`** (new): no path filter, one job `scope`, which classifies the diff,
  prints `class=`/`job=` lines and runs the docs gates (`ci-lint`, `check-docs`, `check-wiring`,
  `check-issue-bodies`, `ci-openspec`). One pinned `uses:` (the same checkout SHA `ci.yml` uses).
- **`tests/test_ci_scope.py`**: 33 cases, including the two anti-drift assertions and the `scope.yml` shape.

## Why

Measured 2026-10-28: a one-file docs PR (#767) and a seven-file docs PR (#825) each queued the same job
set, engine-base rows and scanner builds included. `ci.yml` had 21 `if:` conditions and no path filter —
conditionality was about what is *published*, never about what *changed*.

## Decisions

- **Selection at the trigger, never `if:` on a job.** A job-level condition that skips a stage is invisible
  in the job list and the repo's invariant (`test_no_ci_step_or_job_is_skipped`) allows five shapes, none
  of them a path filter. So the docs class is excluded before any job exists, and `scope` carries the
  legibility: it always runs and states which stages the diff selected.
- **`git diff`, not a path-filter action.** A third-party `uses:` needs a 40-hex pin, a `docs/SECURITY.md`
  row and a roster entry, and it would put the power to skip the pipeline behind a dependency.
- **The table is today's graph.** #824's 28-job table predates #871; naming thirteen deleted jobs would
  have been worse than no classifier. A test asserts every named job exists in `ci.yml`.
- **`push` keeps the whole matrix** — `paths-ignore` is a `pull_request` decision; `main` is never
  under-tested.
- **The scanners over-select on an engine change.** `scanner-images` keys on `containers`, and
  `containers/engines/**` is a containers path, so an engine-params change also builds the scanners. That
  is the granularity the issue specifies; the test records it rather than asserting a sharper rule the
  repo does not have, and sharpening belongs to part (b).
- **`cancel-in-progress` is evaluated, never a bare `true`** — the repo's own concurrency gate caught the
  bare form in the first draft of `scope.yml`, which is exactly the guard doing its job.

## Gates

- `tests/test_ci_scope.py` + the workflow-hygiene suite (`ci_concurrency`, `ci_images`, `workflows_valid`,
  `pin_actions`, `dispatch_forms`, `workflow_guards`) — 130 passed.
- `make check-workflows`, `check-wiring` (100 CI-called targets), `check-docs`, `lint`,
  `openspec-validate NAME=ci-path-scope`, `openspec-tasks-check` — green.
- Measured selections: docs-only → 3 of 15 jobs; engine params → 13 of 15; unmatched path → exit 1.

## Related

Issue [#824](https://github.com/asimov-agent/llgenie/issues/824) (part a) · #871 (the macOS deletion this
table reflects) · #817 (queue starvation, the other lever) · #801 / #817 (an absent check read as a
verdict — why `scope` is always present).
