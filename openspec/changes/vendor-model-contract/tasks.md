# Tasks — vendor-model-contract

- [x] 1. `scripts/sync_registry.py`: `UPSTREAM_CONTRACT` / `UPSTREAM_CONTRACT_DOC` / `VENDORED_CONTRACT` / `VENDORED_CONTRACT_DOC`; `sync()` fetches and writes both contract files, and the "unchanged" test covers them.
- [x] 2. `scripts/sync_registry.py`: `check_contract(data, schema)` reads `required`, `pattern`, `enum` and `minItems` from the vendored schema and names the offending row; `check()` requires the vendored contract and calls it before the README checks.
- [x] 3. `data/model_contract.json` + `data/MODEL_CONTRACT.md` vendored byte-identical to upstream; `Makefile` help lines and the README registry section mention the contract.
- [x] 4. `tests/test_trend_pick.py`: sync writes both files and is idempotent; a missing vendored contract is refused; a row missing `last_seen`, a bad `id`, a bad `backend` and a `formats[0]` without `hf` are each refused by name; the vendored copies equal upstream and the vendored store passes.
- [x] 5. Proven red-first: the five new tests fail on `origin/main`'s `sync_registry.py` (`5 failed`, `AttributeError` on the missing seam) and pass with the change (`5 passed`).
- [x] 6. Measured: `make check-registry` OK on the committed 23-model store (`contract satisfied`) and the freshly synced 106-model store satisfies the vendored contract + README order.
- [x] 7. `agent-wiki/2026-10-26-vendor-model-contract.md` + a `CHANGES.md` row name #694; `make check-docs` ok, `make lint` ok, `make check-wiring` ok.
- [x] 8. `make test-unit` green (`5245 passed, 6 deselected`, 868.53s — rebased onto `main` @ `0aeb77c`, so it also carries #692's and #696's tests) and `make openspec-validate NAME=vendor-model-contract` exits 0.
