# The heavy top-tier row stops running on pull requests

## Why

Three rows were the long poles of every pull request. Two of them — `macos / unit` and
`macos / top-tier` — are already gone: `ci.yml` has no `macos` group any more, removed by deletion
rather than by a condition (**#870**), so no macOS runner is requested at all.

What is left is `linux / top-tier`. It downloads and serves a **real model** on every pull request.
What it proves — that a host can fetch a model and answer on the OpenAI API through the engine
image — is a property of `main` and of the weekly engine/registry data, not of an arbitrary diff,
and it is one of the longest rows in the matrix. Measured on `#767`'s run `40694228407`, a **one-file
documentation PR**: `26 success · 1 skipped · 0 failed`, with the run held open on a heavy row alone.

## What Changes

- **`scripts/ci_slow_rows.py`** (`make ci-slow-rows`) decides, once, whether `top-tier` runs in this
  run: a `pull_request` without the `ci:slow` label gets the `["none"]` placeholder; every non-PR
  event (a `push` to `main`, a dispatch, an unknown/empty event) gets `["run"]` — fail closed, so
  only a PR can lose the row.
- **`ci.yml`'s `guard` job** runs the decision and publishes `top_tier_rows`; the `linux` caller
  passes it into the shared `pipeline.yml` (`needs: [ci-images, guard]`).
- **`pipeline.yml`'s `top-tier` job** takes that list as its ONE matrix axis. A placeholder row runs
  **no make target** and its one unguarded step prints `[slow-rows] … = NOT SCHEDULED` with the
  reason. No job-level `if:` — `tests/test_ci_images.py::test_no_ci_step_or_job_is_skipped` forbids
  it, and a skipped job would make the check name disappear.
- **Opt-in:** a PR that needs the row carries the `ci:slow` label; the next run of that PR (a push,
  a close/reopen) schedules it.
- **Documentation:** `docs/BOTS.md` states which row is main-only + opt-in, what it costs when
  requested, what did **not** change (`linux / unit` is still the PR gate for the suite,
  `linux / cpu-health` still serves the 0.5B model on a PR), and that the macOS rows are gone by
  deletion (#870). The `ci.yml` header carries the same decision next to the trigger it applies to.

## Impact

- A PR no longer pays the heaviest row in the matrix for a property that `main`'s own runs and the
  weekly engine/registry runs already cover.
- Nothing is lost silently: the row runs on every merge to `main` and on demand via `ci:slow`; the
  run log states the decision and an unscheduled row identifies itself.
- `tests/test_ci_slow_rows.py` pins the decision (PR/label/push/dispatch/unknown events, the label
  payload shapes) and the wiring (guard output → the caller → the matrix axis → no working step on
  the placeholder), and checks that `unit` / `cpu-health` gained no row gate.

## Not covered

- Restoring an on-demand full-matrix workflow_dispatch for `ci.yml` — the file has no
  `workflow_dispatch` trigger and its `name:` is matched verbatim by three `workflow_run` consumers,
  so adding one is a separate change.
- A weekly home for the `top-tier` row — that is #861, parked behind this change.
- `concurrency:` in `ci.yml` — that is #858, the owner's decision.
- Runner-minute quotas/billing, and any other row or workflow.
