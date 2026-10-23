# Tasks — reactor-route-fork-pr

- [x] 1. OpenSpec change
- [x] 2. `scripts/run_failure_reactor.py`: resolve the PR for an empty `pull_requests` (head branch +
      owner via `scripts/resolve_run_pr.py`), route the trusted fork through
      `fix_bot_sweep.eligible(..., own_fork=TRUSTED_FORK)`, require `DISPATCH_TOKEN` for the dispatch
- [x] 3. `Makefile` (`DISPATCH_TOKEN ?= $(GH_TOKEN)` + `export`) and the workflow step's
      `DISPATCH_TOKEN: ${{ secrets.BUMP_TOKEN }}`
- [x] 4. `tests/test_run_failure_reactor.py`: fork dispatch + owner token, missing token loud, fifth-party
      fork, draft fork, same-repo unchanged
- [x] 5. README + agent-wiki
- [x] 6. Verified: `pytest tests/test_run_failure_reactor.py` → 13 passed
