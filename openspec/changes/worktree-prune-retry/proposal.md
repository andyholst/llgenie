# A branch held by a worktree is a keep, not an Error 2

## Why

`make worktree-prune` is the documented post-merge step (AGENTS.md, #431). After #592 it still exited
**2** on this checkout, forever, on one branch:

```
[worktree-prune] FAILED: fix/rebase-behind-despite-comment: could not delete the branch:
  git branch -D … failed: cannot delete branch 'fix/rebase-behind-despite-comment'
  used by worktree at '/home/asimov/repository/git/llgenie-wt/rebase-behind-despite-comment'
```

The facts (measured, issue #593): the branch tip is `e13f84f`, the worktree's HEAD is `2627d15` — **not**
the tip — and `worktree list --porcelain` reports that worktree as pure `detached` with **no branch
line**. `git rev-parse --symbolic-full-name HEAD` inside it answers `HEAD` (detached), and the directory
carries unmerged entries (`AA`). So the planner cannot see, from the listing it reads, that git will
refuse; the refusal surfaces only at apply time.

#570's tip-match therefore cannot cover it, and ancestry cannot either (that HEAD is on `origin/main` and
not in the branch's history; adopting by ancestry would also adopt every worktree parked on old `main`).

## What changes

`apply()` treats `git branch -D`'s own refusal as the evidence, and splits it two ways:

1. **removable debris** — the refusal names a worktree that `worktree list --porcelain` reports as
   detached, branch-less and clean: remove that directory and retry the delete **once** (a second
   refusal stays an error, naming it);
2. **not ours to touch** — a worktree with a branch checked out, or holding uncommitted/unmerged work:
   the decision becomes a **keep** with the reason printed, and the run continues. Refusing to touch
   someone's half-merged tree is the planner's own documented behaviour for a dirty worktree; making the
   whole sweep exit 2 for it is the defect.

A refusal that names no worktree at all stays an error — nothing is silenced.

## Impact

- `scripts/worktree_prune.py` — `_refused_by_worktree()` and `_detached_and_clean()` (new, pure) and the
  refusal branch in `apply()`; `plan()` unchanged.
- `tests/test_worktree_prune.py` — the three new cases drive the real `apply()` against git's real
  message (a keep, a remove-then-retry, and an unattributable refusal), plus the helpers' contract over a
  real repository with one named and one detached worktree.
- `README.md`, `agent-wiki/` — the refusal rule.

Verified on the actual checkout: `make worktree-prune` now prints
`keep fix/rebase-behind-despite-comment — held by the worktree … (a branch is checked out there, or it
holds uncommitted/unmerged work)` and exits **0**.

Not in this change: #433 (a container run leaves root-owned files in a worktree, which makes
`git worktree remove` fail with `Permission denied`), and `worktree remove --force` as a general answer —
forcing would delete a dirty worktree someone is working in, which is the one thing the guards prevent.
