# ci-scope-select-guard

- [x] `scripts/ci_scope.py`: `select()` raises `ValueError` naming the unknown entries and the valid class set; an empty list stays legal; `classify()`, the job table and every caller unchanged
- [x] `tests/test_ci_scope.py`: the raise (names the bad name and every valid class, names all unknown entries), `select([])` = always-on jobs only, `select(list(CLASSES))` = 10/10; the two raise cases were red (`DID NOT RAISE`) against the old `select()`
- [x] `agent-wiki/` note + `docs/changes.d/` fragment, and `CHANGES.md` re-rendered with `make changes-index`
- [x] `python -m pytest tests/test_ci_scope.py -q` (43 passed) and `make issue-bot-gates-check` green
- [x] `make lint`, `make check-docs`, `make check-wiring` and `make openspec-validate NAME=ci-scope-select-guard` green
