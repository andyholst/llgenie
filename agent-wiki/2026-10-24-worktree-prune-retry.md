# 2026-10-24 — a branch held by a worktree is a keep, not an Error 2 (#593)

Issue: **#593** (implemented here), filed from the run that verified #570/#592. Related: **#570**
(tip-matched detached worktrees, merged as `ddbf9c0`) and **#433** (root-owned files a container leaves in
a worktree, the `Permission denied` removal failure in the same run). PR: this branch's PR against
`asimov-agent/llgenie:main`.

## What was measured

Right after #592 merged, `make worktree-prune` still exited 2 on this checkout:

```
[worktree-prune] FAILED: fix/rebase-behind-despite-comment: could not delete the branch:
  git branch -D … failed: cannot delete branch … used by worktree at '…/rebase-behind-despite-comment'
```

The facts: branch tip `e13f84f`; that worktree's HEAD `2627d15` (**not** the tip, and on `origin/main`);
`worktree list --porcelain` reports it as pure `detached` with **no branch line**;
`git rev-parse --symbolic-full-name HEAD` inside it answers `HEAD`; it carries unmerged entries (`AA`).
So neither #570's tip-match nor an ancestry rule can attribute it — and the refusal only exists at apply
time.

## The decision

`apply()` acts on git's own refusal:

- **removable debris** — the named worktree is detached, branch-less and clean → remove it, retry
  `branch -D` **once** (a second refusal stays an error naming it);
- **not ours to touch** — a branch checked out there, or uncommitted/unmerged work → the decision becomes
  a **KEEP** with the reason printed. That is the planner's own documented behaviour for a dirty
  worktree; exiting 2 for it was the defect;
- a refusal naming no worktree stays an error — nothing is silenced.

No `--force`: forcing would remove a dirty worktree someone is working in, the one thing the guards exist
to prevent.

## Verification

- `tests/test_worktree_prune.py` — 18 pass in the CI test image against real `git` and a stubbed `gh`:
  the real `apply()` driven by git's real message (keep / remove-then-retry with exactly one retry /
  unattributable error), and the helpers over a repository with one named and one detached worktree.
- Proven against the base: with `origin/main`'s `worktree_prune.py` the three new cases fail, the other
  15 pass.
- **On this checkout**: the run now prints `keep fix/rebase-behind-despite-comment — held by the worktree
  … (a branch is checked out there, or it holds uncommitted/unmerged work)` and exits **0**.
- `make test-unit`, `make openspec-validate NAME=worktree-prune-retry`, `make lint`, `make check-docs`.

## Status

The bot never merges; CI's `auto-merge` owns landing.
