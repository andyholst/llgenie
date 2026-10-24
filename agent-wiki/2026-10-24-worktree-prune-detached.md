# 2026-10-24 — a detached worktree is matched to the branch it holds (#570)

Issue: **#570** (implemented here). PR: this branch's PR against `asimov-agent/llgenie:main`.

## What was measured

`make worktree-prune` ran twice on this host after two PRs merged (#590, #591) and needed **two** runs to
finish: the first reported `pruned 0 branches, 2 worktrees` (branches intact), the second `pruned 2
branches, 0 worktrees`. The same target had earlier exited 2 forever on one branch:

```
$ make worktree-prune DRY=1
[worktree-prune] would prune fix/rebase-behind-despite-comment — PR #502 merged, its merge commit is on origin/main
[worktree-prune] would prune 1 branches, 0 worktrees
$ make worktree-prune
[worktree-prune] FAILED: … cannot delete branch 'fix/rebase-behind-despite-comment' used by worktree at '…'
```

`git worktree list --porcelain` reports that directory as `detached`.

## Root cause

`plan()` matched worktrees to branches with `{t.branch: t for t in trees if t.branch}`. A **detached**
worktree has no branch name, so it can never be matched — but it is still the checkout that holds the
branch, and `git branch -D` refuses while it exists. So the plan built `Decision(path=None)`, skipped
`git worktree remove`, and the branch delete either failed the sweep (exit 2, forever) or — when git did
allow it — stranded the directory with no ref, which is the shape `apply()`'s own docstring warns
against.

## The decision

A second index in `plan()`: detached worktrees by their HEAD commit. When a prunable branch has no named
worktree, the plan adopts **exactly one** detached worktree whose HEAD is that branch's tip, and from
there it goes through the same guards (main checkout, this run's own worktree, dirty) and the same order
(`worktree remove` first, then `branch -D`). A detached worktree parked on an **unrelated** commit matches
nothing and is left alone — no merge licenses deleting someone's checkout of an older commit.

The existing policy test asserted the old behaviour (keep the directory, delete the branch — the
stranding). It is re-specified as two cases: tip-matched → both removed; elsewhere → untouched.

## Verification

- `tests/test_worktree_prune.py` — 14 pass in the CI test image, against real `git` and a stubbed `gh`
  (the repo's allowance for an external CLI). New: two merged branches pruned in one run, the
  detached-tip branch pruned in one run, and the unrelated detached worktree kept.
- Proven against the base: with `origin/main`'s `worktree_prune.py` swapped in, the two detached cases
  fail and the other 12 pass.
- `make test-unit`, `make openspec-validate NAME=worktree-prune-detached`, `make lint`, `make check-docs`.

## Status

The bot never merges; CI's `auto-merge` owns landing.
