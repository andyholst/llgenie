# Tasks — registry-sync-change-issue

- [x] 1. `scripts/registry_change_issue.py`: `compare()` + `render()` over the six files (store, contract, README, quant catalog, matrix fixture, skill gap) against `--prev-rev`.
- [x] 2. `scripts/registry_change_issue.py`: `open_issue()` files ONE issue labelled `agent:implement` and edits the one carrying the store's marker; `--dry` mutates nothing.
- [x] 3. `Makefile`: `registry-change-report` + `sync-change-issue` in `.PHONY` and `make help`; `.github/workflows/registry-sync.yml`: the step with `if: always() && steps.diff.outputs.changed`.
- [x] 4. `tests/test_registry_change_issue.py`: the report names an added model / new engine / added contract key; one issue per store version (update, not duplicate); `--dry` touches nothing; the workflow's `always()` assertion.
- [x] 5. Measured on real data: `make sync-registry` (23 -> 112 models) then `make registry-change-report` renders the body.
- [x] 6. `README.md` + `docs/BOTS.md` mirror the two targets and the step; `agent-wiki/2026-10-27-registry-sync-change-issue.md` + a `CHANGES.md` row name #704 and the PR.
- [x] 7. `make test-unit` green (`5252 passed, 6 deselected`, 1101.08s), `make check-docs` / `check-wiring` / `check-dispatch-forms` ok, `make openspec-validate NAME=registry-sync-change-issue` exits 0.
