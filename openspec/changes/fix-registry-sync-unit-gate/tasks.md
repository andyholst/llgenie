# Tasks — fix-registry-sync-unit-gate

- [x] 1. Reproduce the failure in the job's own order on `origin/main` (`930900b`): `make sync-registry` (23 -> 112 models), `make sync-quant-catalog`, `make render-trend-list-matrix`, `make render-engine-skill-gap`, `make test-unit` -> `36 failed, 14486 passed`, split into 5 families.
- [x] 2. `scripts/gen_trending_quant_catalog.py`: `_repos_for()` applies `plan_download()`'s repo-naming rule (`mlx` in the repo name iff the format is `mlx-safetensors`); a Strata cell is generated only when `strata_serves(model)`.
- [x] 3. `tests/test_trending_quant_catalog.py`: hermetic cases for both rules (`test_a_safetensors_cell_is_planned_only_from_a_non_mlx_repo`, `test_a_strata_cell_exists_only_for_the_family_strata_serves`).
- [x] 4. `scripts/model_engine_pick.py`: `engine_has_a_plan()` — for a model the committed table covers, `rank_engines` offers only an engine with a cell; a model the table does not cover keeps live resolution.
- [x] 5. `tests/test_model_engine_pick.py`: the two rank-gate cases (covered model drops the plan-less engine, uncovered model keeps its engines).
- [x] 6. `tests/hub_probe.py`: 401/403 classify as `gated` (the file exists, this credential may not read it) — the rule #418 already applies elsewhere; `tests/test_hub_probe.py::test_a_gated_file_verifies_and_says_it_is_gated` proves it.
- [x] 7. `scripts/trend_list_matrix.py` renders the rows `matrix()` actually gated in (`trend_list(registry, vram, ram)`), and `tests/test_trend_list_matrix.py` states the RAM rule as "more RAM only adds rows".
- [x] 8. `tests/test_pick_matrix_arch_perms.py`: the stubbed file disables the committed table (`LLGENIE_QUANT_CATALOG=0`), so a stub id upstream also lists is answered by the stub.
- [x] 9. `tests/test_trending_quant_catalog.py`: the two catalog-coverage rules are stated on `offer()` (what `llgenie` prints), not on the raw rank list — the raw list is #731's own work item.
- [x] 10. `data/unsupported-engines.json`: 18 engines dated and decided from their own upstream READMEs (26 entries total); `make check-engine-skill-gap` reports `unresolved 0`.
- [x] 11. Re-render the synced artifacts in the job's order and commit them together (`data/models.json`, `data/trending-README.md`, `data/trending-quant-catalog.json` + fixture, `tests/fixtures/trend-list-matrix.json`, `data/engine-skill-gap.json`).
- [x] 12. `make check-registry check-quant-catalog check-trend-list-matrix check-engine-skill-gap` and `make skills-validate REGISTRY=data/models.json UNSUPPORTED=data/unsupported-engines.json` are green on the synced files.
- [ ] 13. `make test-unit` green on the synced store (the gate the sync job's own step 9 runs).
- [x] 14. `make openspec-validate NAME=fix-registry-sync-unit-gate` exits 0.
- [x] 15. Docs: README's registry-sync section states what the gate now guarantees; `agent-wiki/2026-10-27-registry-sync-unit-gate.md` records the change; `CHANGES.md` carries its row; `make check-docs` green.
- [ ] 16. OpenSpec validation green and the change recorded in `CHANGES.md` / `agent-wiki/` in the same commit batch.
