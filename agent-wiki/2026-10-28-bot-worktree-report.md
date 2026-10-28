# 2026-10-28 — the bench is reported before a bot starts, and the prune is gated

Issue: [#794](https://github.com/asimov-agent/llgenie/issues/794) — PR: [#847](https://github.com/asimov-agent/llgenie/pull/847)

## What was wrong

A host bot started work blind. `AGENTS.md` mandates a fresh worktree per agent and every agent stops
at the PR, so no bot step ever sees a merge; leftover directories accumulated unseen — measured on the
owner's host at `main@17cdcf3`: **37 worktrees** under `/home/asimov/repository/git/llgenie-wt/`,
**7** on a branch already in `origin/main` with no open PR, **23** off-main with no open PR.

The only cleanup target, `make worktree-prune`, DELETES directories and cannot see uncommitted work:
a worktree mid-flight whose branch tip is already an ancestor of `main` looks identical to a finished
one. On this host a prune did exactly that — it deleted the #791 run's worktree at 16:07Z with
uncommitted work in it. `AGENTS.md:483` told an unattended agent to run that target.

## What changed

- `scripts/worktree_report.py` + `make worktree-report` — measure only. Per `git worktree list
  --porcelain` entry: path, branch (`detached` when it holds none), `merged-into-main` (a real
  `git merge-base --is-ancestor <head> <base>`), `open-pr` (one real `gh pr list`, keyed by the PR's
  head branch) and `dirty` (a real `git status --porcelain` in that directory), then a summary of
  `total`, `stale` (merged, no open PR, not the main checkout), `off-main-no-pr` and `dirty`. No
  `git worktree remove`, no `git worktree prune`, no `git branch -D`. Exit 0 when nothing is stale;
  exit 2 naming the step when a measurement fails, because an unreadable state is not a clean state.
- `scripts/worktree_prune_guard.py`, run as the first recipe line of `make worktree-prune` — a bot run
  (`CI` or `BOT` set, a falsey value does not count) is REFUSED with exit 3 unless `CONFIRM=1`,
  naming `make worktree-report` and the re-run spelling. The owner's run (neither variable set) is
  unchanged, and `CONFIRM=1` lets a bot proceed exactly as today. `scripts/worktree_prune.py`'s own
  eligibility logic is untouched (the root-owned-debris half is #759).
- `.hermes/skills/bot-unattended/SKILL.md` and `.hermes/skills/issue-implement/SKILL.md` — the
  prohibition in both Rules sections: report with `make worktree-report`, and never run
  `make worktree-prune` / `git worktree prune` / `git worktree remove` unless the owner says so.
- `docs/BOTS.md` — both targets documented, so `make check-docs` stays green.

## Decisions

- **One bulk `gh pr list`, not one call per worktree.** The report reads every open PR once and keys
  it by `headRefName`; a per-branch call would be N authenticated API calls for the same answer.
- **The main checkout is never "stale".** It is merged-into-main by definition and owns no PR, so
  counting it would make every clean repository report one finding. The row says `(main checkout)`
  and the summary excludes it.
- **A missing path counts as dirty.** A worktree git still lists but whose directory is gone cannot be
  proven clean, so the row says `dirty=yes (path missing)` rather than inventing a clean verdict.
- **A failing `gh` fails the report (exit 2).** Reporting `open-pr=no` when the lookup never answered
  would invite exactly the destructive decision the report exists to prevent.

## OWED

- **`AGENTS.md:483`** still instructs the prune. This session's write gate refuses edits to a
  protected agent-instruction file with no user present, so the exact intended replacement is in the
  PR body (issue #794's criterion 4 escape hatch).
- **`agents/llgenie-planner/SOUL.md` and `agents/llgenie-issse-implementer/SOUL.md`** (criterion 5) —
  those paths arrive with #791 (PR #834), which is still open; the edit is owed to the run that sees
  them on `main`.

## Verified

- `tests/test_worktree_report.py` — 10 passed in the test image: the four measured facts against a
  real repository with real worktrees, `git worktree list` and the branch set byte-identical before
  and after the report, a clean checkout exiting 0, a failing `gh` exiting 2, the guard's four
  directions, the Makefile wiring, and both skills' prohibition.
- `make test-unit` in `llgenie/test:latest`: **14562 passed, 6 deselected in 3508 s**, exit 0 (two
  earlier attempts were killed by the host with Error 137 — the suite is memory-heavy here).
- On this host: `make worktree-report` printed 48 worktrees, `summary total=48 stale=13
  off-main-no-pr=26 dirty=9`; `BOT=1 make worktree-prune` and `CI=true make worktree-prune` both
  refused naming `make worktree-report`; `BOT=1 make worktree-prune CONFIRM=1 DRY=1` and
  `make worktree-prune DRY=1` both printed the plan ("would prune 3 branches, 1 worktrees; kept 79").
