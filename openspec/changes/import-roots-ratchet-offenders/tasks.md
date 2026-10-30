# import-roots-ratchet-offenders

- [x] `scripts/check_import_roots.py`: over-count items carry `over` + `sites`, and `render_ratchet()` prints the aggregate line plus each `file:line`
- [x] `tests/test_import_roots.py`: a planted root reds naming that `file:line`; no extra root is green; a removed root is green; `report` still lists findings
- [x] `agent-wiki/` note + `docs/changes.d/` fragment, `CHANGES.md` re-rendered with `make changes-index`
- [x] `make check-import-roots`, `make lint`, `make check-docs`, `make check-wiring`, `make check-pr-hygiene`, `make openspec-tasks-check`, `make test-unit` and `make openspec-validate NAME=import-roots-ratchet-offenders` green
