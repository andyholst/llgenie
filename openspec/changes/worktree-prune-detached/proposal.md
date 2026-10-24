# A detached worktree is matched to the branch it holds

## Why

`make worktree-prune` is the documented post-merge step (AGENTS.md, issue #431): it removes the worktree
and local branch of every MERGED pull request, proven by the PR's merge commit rather than by ancestry
(this repo squash-merges, so a branch tip is never an ancestor of `main`).

It matches a worktree to a branch through `{t.branch: t for t in trees if t.branch}`. A worktree git
reports as **detached** carries no branch name, so it can never be matched — while it is still the
directory that holds that branch's checkout. Measured on the real checkout (issue #570):

```
$ make worktree-prune DRY=1
[worktree-prune] would prune fix/rebase-behind-despite-comment — PR #502 merged, its merge commit is on origin/main
[worktree-prune] would prune 1 branches, 0 worktrees        # ← a branch WITH a worktree, promising none
$ make worktree-prune
[worktree-prune] FAILED: … git branch -D … failed: cannot delete branch
  'fix/rebase-behind-despite-comment' used by worktree at '…/rebase-behind-despite-comment'
make: *** [Makefile:676: worktree-prune] Error 2
```

Two consequences, both wrong:

- **the plan contradicts the evidence** — it prints `0 worktrees` for a branch that has one, because the
  detached worktree fell out of the mapping;
- **the sweep exits 2 forever** — `git branch -D` refuses while that directory exists, so the target can
  never be green on this checkout and anything chaining it with `&&` stops there.

The module's own `apply()` warns about exactly this shape ("deleting the branch first would strand the
worktree with no ref"). And the opposite order is what the current code accidentally produces for a
detached worktree created at the branch tip: the branch is deleted and the directory is stranded.

## What changes

`plan()` builds a second index — detached worktrees by their HEAD commit — and, when a prunable branch
has no named worktree, adopts **exactly one** detached worktree whose HEAD is that branch's tip. From
there it is treated like any other worktree: the main-checkout guard, the "this run's own worktree"
guard, the dirty-worktree guard, `git worktree remove` first, then `git branch -D`.

The rule stays conservative on purpose: a detached worktree parked on an **unrelated** commit matches no
branch and is left alone — nothing about a merged PR licenses deleting someone's checkout of an older
commit.

The existing policy test (`test_a_detached_worktree_is_never_removed`) asserted the old behaviour —
keep the directory, delete the branch — which is the stranding this fix removes. It is re-specified as
two cases: a detached worktree on the merged tip is removed **with** its branch, and a detached worktree
on another commit is never removed.

## Impact

- `scripts/worktree_prune.py` — `plan()`'s detached index and the adoption rule; `apply()` unchanged
  (it already removes the worktree before deleting the branch when a path is known).
- `tests/test_worktree_prune.py` — the re-specified policy test, a new "one run, both gone" case, a new
  "detached elsewhere is untouched" case, and a two-branch single-run case.
- `README.md`, `agent-wiki/` — the prune's documented matching rule.
