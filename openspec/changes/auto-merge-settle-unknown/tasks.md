# Tasks — auto-merge-settle-unknown (issue #558)

- [x] 1. OpenSpec change: `proposal.md`, `specs/auto-merge-settle-unknown/spec.md`, this checklist
- [x] 2. `scripts/auto_merge.py`: `settle_mergeable()` + `run()` calls it before deciding
- [x] 3. `.github/workflows/auto-merge.yml`: the `recheck` job runs on every CI completion (`needs: [merge]`, `always()`), cron kept
- [x] 4. Tests: UNKNOWN settles → merges without `--admin`; UNKNOWN forever → bounded then defer; the recheck wiring
- [x] 5. `README.md` + `agent-wiki/2026-10-23-auto-merge-settle-unknown.md`
- [x] 6. Verified: `pytest tests/test_auto_merge.py tests/test_dispatch_forms.py tests/test_workflow_guards.py` → 88 passed; `make lint`, `make check-workflows`, `make check-docs`, `make openspec-validate NAME=auto-merge-settle-unknown`, `make openspec-tasks-check`; `make test-unit` in the PR checks
- [x] 7. PR opened against `asimov-agent/llgenie:main` closing #558
