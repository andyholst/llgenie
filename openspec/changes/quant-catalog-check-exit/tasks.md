# Tasks — quant-catalog-check-exit

- [x] 1. `tests/test_script_exit_codes.py`: ast-based guard — a `__main__` that calls `main()` bare requires `main()` never to `return` a value; proven red on the current tree (names `gen_trending_quant_catalog.py`).
- [x] 2. `scripts/gen_trending_quant_catalog.py`: `raise SystemExit(main())`.
- [x] 3. `make sync-quant-catalog` regenerates `data/trending-quant-catalog.json` + its fixture (the table the broken check was hiding).
- [x] 4. Measured: `make check-quant-catalog` exits 1 before the fix on the stale table, exits 0 after it on the regenerated one.
- [x] 5. `agent-wiki/2026-10-27-quant-catalog-check-exit.md` + a `CHANGES.md` row name #701 and the PR; `make check-docs`, `make lint`, `make check-wiring` ok.
- [x] 6. `make test-unit` green (`5250 passed, 6 deselected`, 772.96s) and `make openspec-validate NAME=quant-catalog-check-exit` exits 0.
