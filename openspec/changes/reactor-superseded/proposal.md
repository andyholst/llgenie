# Route B files only work that is still work

## Why

The run-failure reactor (`scripts/run_failure_reactor.py`, issue #286) reacts to a failed CI run by
routing it: **Route A** dispatches the fix-bot when the run's PR is pushable, and **Route B** files a
tracked issue labelled `agent:implement` when no pushable PR exists.

Route B never asks whether the subject of the failure still exists. It collapses two different states
into one decision:

- the PR is **open** but not pushable right now — a draft, or its repair attempts are spent — so the
  failure is still work, and filing is right;
- **no open PR exists at all** — the PR merged or was closed and its branch deleted — so the failure is
  history, and filing is wrong.

Measured on `main` on 2026-10-23, all six `agent:implement` issues the reactor had filed were the second
state: `#557`→PR #554 merged 10:09Z, `#551`/`#542`→#539 merged 09:12Z, `#537`→#533 merged 05:26Z,
`#507`→#506 merged 2026-10-22 09:44Z, and `#548` a red `push` run on `main` whose next run of the same
workflow on the same branch concluded `success` at 10:19Z. **6 of 6 were noise.**

The cost is the implementer's budget: `scripts/issue_implementer.py` takes `MAX_PER_DAY = 3` issues a
day, oldest-first, so six reactor duplicates spend two full days of agent time re-deriving failures that
were green before their issues existed — and each of those issues sat in front of real work.

## What changes

Route B gains **one deterministic decision**, evaluated only on its own path (after Route A has already
found no pushable PR):

1. **A `pull_request`-event run is filed only when an OPEN PR exists for its head.** The check reuses
   `scripts/resolve_run_pr.open_pr_for_head` — the same resolver auto-merge and the reactor's own fork
   path already use — so a merged or closed PR, or a deleted branch, means "nothing left to repair" and
   files nothing.
2. **A `push` run is filed only when no LATER run of the same workflow on the same branch concluded
   `success`.** A later green run on that branch is proof the failure was transient or already fixed.

The verdict is a loud, greppable decision line — `[run-fixer] run <id> is SUPERSEDED: <reason> - filing
nothing` — never a silent skip, because a silent skip is indistinguishable from a crash (issue #312).

The dedupe marker stays sha-scoped. A same-job failure on a *different* head can be a different defect
(measured: `macos / unit` failed on the engine-image digest, the README dispatch table and the cron
collision, all within six hours), so collapsing by workflow/job alone would lose distinct work. The
cross-issue sweep is #563's problem, not this change's.

Nothing else moves: Route A is untouched, the claim protocol is untouched, no token or dispatch path
changes, and the reactor still never repairs, commits, pushes or merges.

## Impact

- `scripts/run_failure_reactor.py` — `superseded()` (new), `route()` (one call on the Route B path),
  `run_detail()` (reads `createdAt`, needed to order runs).
- `tests/test_run_failure_reactor.py` — the four new scenarios, driven through the real `route()` with
  a stubbed `gh` on `PATH`.
- `README.md`, `agent-wiki/` — the reactor's documented behaviour, which currently says Route B files
  unconditionally.
