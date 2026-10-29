# The heavy top-tier row left the pull_request matrix (issue #859)

## What changed

`linux / top-tier` no longer runs on a `pull_request`. It runs on every non-PR event (the `push` to
`main`, so one run per merge still catches a model/engine regression) and on a PR that carries the
**`ci:slow`** label.

The selection is one decided value, not an expression spread over two workflows:
`scripts/ci_slow_rows.py` (`make ci-slow-rows`) takes the event and the PR's labels and returns
`["run"]` / `["none"]`. `ci.yml`'s `guard` job runs it and publishes `top_tier_rows`; the `linux`
caller passes it into the shared `pipeline.yml`, whose `top-tier` job takes that list as its ONLY
matrix axis. Nothing else gained a gate: `linux / unit` is still the PR gate for the whole suite and
`linux / cpu-health` still serves the 0.5B model through the engine image on a PR.

## The scope moved under the change, and the change moved with it

When the branch was cut, issue #859 named three rows: `macos / unit`, `macos / top-tier` and
`linux / top-tier`. While the branch was being built, **#870** landed on `main` and removed the whole
`macos` group from `ci.yml` — by deletion, not by a condition — so two of the three rows no longer
exist and no macOS runner is requested at all. The rebase kept the one row that is still a PR cost
and dropped the machinery the deletion made pointless (a `unit` row axis, and the
`runs-on`-redirect for a placeholder on a macOS label). The docs now say the macOS half is #870's
deletion rather than something this change gates, so a reader is not told about rows that are gone.

## Setup that had to be honoured

- **No job-level `if:`** — `tests/test_ci_images.py::test_no_ci_step_or_job_is_skipped` refuses it,
  and a skipped job makes its check name disappear. The repo's sanctioned shape is the `["none"]`
  placeholder row (`engine-image-none`, `test-published-*-none` already do this), so `top-tier`
  gained a `row` axis and every working step is gated on `matrix.row != 'none'`.
- **An absent row is stated, never silent.** The one unguarded step prints
  `[slow-rows] top-tier on ubuntu-latest = NOT SCHEDULED: …`, and the decision line from
  `make ci-slow-rows` names the state in the guard job's log.
- **`slow` is not published as a guard output.** The first version declared it and
  `tests/test_workflow_guards.py::test_no_guard_declares_an_output_nobody_reads` redded: a value
  nothing consumes is a promise nobody keeps. The boolean is read in the run log instead.

## Verification

- `tests/test_ci_slow_rows.py` drives the decision itself (PR without the label, PR with `ci:slow`,
  push/dispatch/schedule/unknown/empty events, an unrelated label, the label payload shapes) and
  pins the wiring: guard output → the caller → the matrix axis → no working step on the placeholder,
  plus the untouched `unit` / `cpu-health` gates and the documented trade.
- The negative control: with `.github/workflows/{ci,pipeline}.yml` reverted and the tests kept, the
  wiring tests red (`test_ci_yml_publishes_the_decision_and_the_caller_consumes_it`,
  `test_the_top_tier_row_is_the_only_axis_and_runs_no_work_when_absent`,
  `test_the_coverage_trade_is_written_down`); restored, all green. A rule only run on the fixed tree
  has demonstrated nothing.
- Three existing tests pinned the OLD step conditions / caller `with:` and were updated with the
  reason in place: `tests/test_ci_images.py`, `tests/test_macos_install.py`,
  `tests/test_workflows_valid.py`.

## Status

Green locally: `check-workflows`, `check-wiring`, `check-docs`, `check-issue-bodies`,
`check-dispatch-forms`, `check-actions`, `openspec-tasks-check`, `lint`, the affected test modules and
`make test-unit` in `llgenie/test:latest`, `openspec-validate`. The behaviour is proven by the
pushed PR's own runs, whose id pair (placeholder run / `ci:slow` re-run) is recorded in the PR body.

Not touched: `concurrency:` (#858, the owner's decision), a weekly home for `top-tier` (#861, parked
behind this change), and a `workflow_dispatch` trigger for `ci.yml` (its `name:` is matched verbatim
by three `workflow_run` consumers, so adding one is its own change).
