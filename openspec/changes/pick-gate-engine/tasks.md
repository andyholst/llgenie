# Tasks — pick-gate-engine

- [x] `fits()` gates on `vram_min`, falling back to `vram_tier` (#669), and applies `system_ram_min`.
- [x] `llgenie --trend` passes the host's RAM to `offer()` (#414).
- [x] `_canon_format` folds spelling (`LiteRT-LM` → `litertlm`) so a real format is not dropped (#730).
- [x] `tests/test_trend_list_acceptance.py` asserts the fitting set from `mp.fits()` and finds the VRAM column by header (#693).
- [x] `tests/test_pick_matrix_arch_perms.py`, `tests/test_card_aware_rank.py`, `tests/test_mac_trend_pick.py` derived from `offer()` and the store.
- [x] `tests/test_trend_pick.py` de-pinned: derived rows, `_fits_names`, positional line matching, CUDA-cell rename, no model names.
- [x] `tests/test_tensorfold_seamless.py` picks the row the store lets TensorFold serve.
- [x] `make sync-registry` + `make check-registry` + `make check-registry-keys` green on the 2026-10-27 store (112 models, contract satisfied, links answer).
- [x] Verified on the synced store: acceptance 83 passed, arch_perms 74, trend_pick 90, tensorfold 36, mac 18, card_aware 14 — all zero failures.
- [x] `tests/test_trending_quant_catalog.py` 5 passed / 2 failed — the residue is #731 (an engine offered with no downloadable plan), not a pin.
- [x] The branch carries no file under `data/`: the store lands through the sync PR.
