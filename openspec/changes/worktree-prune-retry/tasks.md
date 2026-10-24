# Tasks — worktree-prune-retry

- [x] 1. `scripts/worktree_prune.py`: `_refused_by_worktree()` reads the path out of git's refusal, `_detached_and_clean()` proves the debris shape from `worktree list --porcelain`.
- [x] 2. `scripts/worktree_prune.py`: `apply()` removes a clean detached holder and retries the delete once; a holder the prune may not touch becomes a printed KEEP; a refusal naming no worktree stays an error.
- [x] 3. `tests/test_worktree_prune.py`: the real `apply()` against git's real message — keep, remove-then-retry (exactly one retry), and the unattributable error — plus the helpers over a real repo with a named and a detached worktree.
- [x] 4. Proven against the base: with `origin/main`'s `worktree_prune.py`, the three new cases fail and the other 15 pass.
- [x] 5. Verified on THIS checkout: `make worktree-prune` prints the keep for `fix/rebase-behind-despite-comment` and exits 0.
- [x] 6. README + `agent-wiki/2026-10-24-worktree-prune-retry.md` state the refusal rule and name #593 / the PR.
- [x] 7. `make test-unit` green and `make openspec-validate NAME=worktree-prune-retry` exits 0.
