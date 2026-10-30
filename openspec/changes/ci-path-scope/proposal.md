# ci-path-scope — proposal

Issue: [#824](https://github.com/asimov-agent/llgenie/issues/824) (part a)

## Why

`ci.yml` runs one pipeline for every change. Measured 2026-10-28: a one-file docs PR (#767) and a
seven-file docs PR (#825) each scheduled the **same** job set, engine-base rows and scanner builds
included, for a diff that could not affect either. Review latency is then governed by matrix size rather
than by how much work the change is, and every push re-queues the full set (the queue starvation #817).

`ci.yml` has 21 `if:` conditions and no path filter anywhere: conditionality is about *what is published*,
never about *what changed*. And a job-level `if:` that skips a stage is the wrong tool anyway — it is
invisible in the job list, and `tests/test_ci_images.py::test_no_ci_step_or_job_is_skipped` allows exactly
five such shapes, none of them a path selection.

## What Changes

- `scripts/ci_scope.py` classifies a diff into nine classes (`docs, skills, workflows, scripts, tests,
  data, containers, engines, security`), with ten **wildcard** paths that select every class (`Makefile`,
  `tools/**`, `.github/**`, `scripts/ci_*.py`, `scripts/engine_*.py`, `scripts/check_*.py`, `pytest.ini`,
  `.gitleaks.toml`, `renovate.json`, `AGENTS.md`) — a wrong skip there would hide a regression in the gate
  itself. An unmatched path is **exit 1 naming the path**, never a silent pass.
- The classifier's job table is `ci.yml` **as it is today** — 15 jobs, Linux-only, after #871 deleted the
  macOS group — and a test asserts every job it names exists in the workflow, so the table cannot describe
  a graph the repository no longer has.
- `ci.yml` selects the docs class at the **trigger** (`pull_request.paths-ignore`, the `docs` class minus
  its wildcards, `AGENTS.md` re-included), so a docs-only PR starts no `ci.yml` run at all.
- `.github/workflows/scope.yml` — no path filter, one job named `scope`, one always-present check that
  classifies the diff, prints the classes and every job's verdict, and runs the docs gates (`ci-lint`,
  `check-docs`, `check-wiring`, `check-issue-bodies`, `ci-openspec`). No new third-party action.

## Decisions

- **`git diff`, not a path-filter action.** A third-party `uses:` would need a 40-hex pin, a
  `docs/SECURITY.md` row and a roster entry — and it would put the power to skip the whole pipeline behind
  a dependency this repo has to trust. `git diff --name-only origin/<base>...HEAD` is auditable inside the
  workflow and needs no pin.
- **Selection before jobs exist, not `if:` on a job.** The repo's own invariant stays untouched: no new
  allowlisted `if:` value, no skipped stage hidden in the job list.
- **`push` keeps the full matrix.** `paths-ignore` applies to `pull_request` only; `main` must never be
  under-tested.
- **The classifier's table is today's graph, not the issue's.** #824's table predates #871; a table naming
  `macos/*` and four `engine-base-*` rows would have been describing thirteen jobs that no longer exist.

## Out of scope

- Per-stage selection inside `ci.yml` for the code classes (part b): it needs `pipeline.yml` to accept a
  stage list and changes the job graph part (a) is still proving.
- Making any check *required* in branch protection: deliberately still none; `scope` buys legibility, not a
  second place to maintain a required-check list.
