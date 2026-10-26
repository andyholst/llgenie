# Tasks

- [x] 1. Measured the block (issue #687): upstream writes model/recipe names into `formats[].name`; on that store `model_engine_pick` cannot resolve a plan (`use_format: safetensors`, `StopIteration`) and the sync's `make test-unit` step reds 101 tests
- [x] 2. `scripts/sync_registry.py`: `FORMAT_VOCAB`, `_canon_format`, `_format_from_repo`, `normalise_formats`, `normalise` (vocabulary + repo/id inference + duplicate-id drop), and `sync()` writing the normalised store with one printed note per departure
- [x] 3. Rows are NOT folded: measured that a name heuristic merges distinct entities (28 rows folded, finetunes included) and that upstream's README lists them as separate models — documented instead of implemented
- [x] 4. `tests/test_registry_normalise.py`: junk format restated from the repo, MLX row kept MLX, canonical dedupe, distinct rows kept, duplicate id dropped, and a real `sync()` writing a store `validate()` accepts
- [x] 5. Docs: `AGENTS.md` (the normalisation and why folding is refused), `README.md` (the two "verbatim" claims), `docs/BOTS.md` (the sync section)
- [x] 6. Verified against the REAL store: `make sync-registry` writes 106 normalised rows with 83 printed notes; `scripts/registry_keys.py` exits 0 (additive only, 81 drift notes); `make check-registry` passes
- [x] 7. `agent-wiki/2026-10-26-registry-normalise-on-vendor.md` + its `CHANGES.md` row
- [ ] 8. Gates: `make test-unit`, `make check-docs`, `make check-workflows`, `make check-wiring`, `make lint`, `make openspec-validate NAME=registry-normalise-on-vendor`
