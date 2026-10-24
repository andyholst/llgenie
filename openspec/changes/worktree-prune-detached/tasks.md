# Tasks — worktree-prune-detached

- [x] 1. `scripts/worktree_prune.py`: `plan()` indexes detached worktrees by HEAD and adopts exactly one whose HEAD is a prunable branch's tip, before the keep-guards, so the worktree is removed first.
- [x] 2. `tests/test_worktree_prune.py`: re-specify the old "never removed" policy test as tip-matched (removed with the branch) plus a new case that a detached worktree on another commit is untouched.
- [x] 3. `tests/test_worktree_prune.py`: a two-branch single-run case, so the plan can never report `0 worktrees` for a branch that has one.
- [x] 4. Proven against the base: with `origin/main`'s `worktree_prune.py` swapped in, the two detached cases fail and the rest pass.
- [x] 5. README + `agent-wiki/2026-10-24-worktree-prune-detached.md` state the matching rule and name #570 / the PR.
- [x] 6. `make test-unit` green and `make openspec-validate NAME=worktree-prune-detached` exits 0.
