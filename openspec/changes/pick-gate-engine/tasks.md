# Tasks — pick-gate-engine

- [x] `fits()` gates on `vram_min`, falling back to `vram_tier` (#669), and applies `system_ram_min`.
- [x] `llgenie --trend` passes the host's RAM to `offer()` (#414).
- [x] `llgenie --trend` prints the VRAM figure the gate read (`mp.vram_label`: `vram_min`, else the tier), so a row admitted at its 12 GB minimum no longer prints `48GB` beside itself (#669) — measured on the host: `Ornith 1.5` 48GB → 16GB, `Qwen3.8-27B` 16GB → 12GB.
- [x] `_canon_format` folds spelling (`LiteRT-LM` → `litertlm`) so a real format is not dropped (#730).
- [x] `tests/test_trend_list_acceptance.py` asserts the fitting set from `mp.fits()` and finds the VRAM column by header (#693).
- [x] `tests/test_pick_matrix_arch_perms.py`, `tests/test_card_aware_rank.py`, `tests/test_mac_trend_pick.py` derived from `offer()` and the store.
- [x] `tests/test_trend_pick.py` de-pinned: derived rows, `_fits_names`, positional line matching, CUDA-cell rename, no model names.
- [x] `tests/test_tensorfold_seamless.py` picks the row the store lets TensorFold serve.
- [x] `make sync-registry` + `make check-registry` + `make check-registry-keys` green on the 2026-10-27 store (112 models, contract satisfied, links answer).
- [x] Verified on the synced store: acceptance 83 passed, arch_perms 74, trend_pick 90, tensorfold 36, mac 18, card_aware 14 — all zero failures.
- [x] `matrix()` resolves the host's RAM when `--ram` is not given, so `llgenie --matrix` applies `system_ram_min` exactly as `offer()` does (measured: `-k any_offer` 9720 passed).
- [x] `make check-registry` green on the freshly synced 2026-10-27 store: `models=112; contract satisfied, README order matches, links answer`; `check-registry-keys`: additive only, nothing lost.
- [x] `tests/test_pick_full_registry.py` de-pinned: the static (model → exact quant filename) edge table and the hand-written RAM ladder are now DERIVED from the store, and the file's `vram_tier` gate is `mp.fits()`.
- [x] `tests/test_registry_sync_trend.py`, `tests/test_model_engine_pick.py` de-pinned: every "does it fit" in a test is `mp.fits()` (never `vram_tier`), the frozen October-5 expectation is derived from the fixture, and the live 48 GB list is derived from the store's own gate.
- [x] The suite is proved on the store the branch actually ships against — `main`'s committed store, 23 models, where `vram_min` and the README column disagree on 8 rows — as well as on the synced 2026-10-27 one (112 models): `test_trend_list_acceptance`, `test_trend_pick`, `test_registry_sync_trend`, `test_model_engine_pick`, `test_trend_list_matrix`, `test_registry_footprint`.
- [x] The README-column assertions allow EITHER stated figure (`vram_min` or `vram_tier`), because which one upstream prints moves with the sync; the gate's preference for the minimum is proved hermetically in `tests/test_registry_footprint.py::test_the_gate_reads_the_stated_minimum_not_the_display_tier`.
- [x] `tests/test_trending_quant_catalog.py` 5 passed / 2 failed — the residue is #731 (an engine offered with no downloadable plan), not a pin.
- [x] The branch carries no file under `data/`: the store lands through the sync PR.
