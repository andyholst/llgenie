# Tasks

- [x] 1. `registry-sync.yml` runs weekly (`17 5 * * 1`), validates with `ALLOW_UNSKILLED=1`, and commits both quant-catalog copies and no skill files.
- [x] 2. `engine_skills.validate(..., allow_unskilled=True)` and `make skills-validate ALLOW_UNSKILLED=1` skip registry engines that have no skill. `make ci-unit` uses that mode for `data/models.json`. The strict fixture validate is unchanged.
- [x] 3. `tests/fixtures/registry-before/` holds the 2026-10-05 `models.json` and README. `tests/test_registry_sync_trend.py` downloads the live upstream with `sync_registry.sync` and checks the 48 GB CUDA before/after ranking, including a real higher skilled t/s.
- [x] 4. Vendored-list tests in `tests/test_trend_pick.py` follow the current file instead of pinning SGLang at 44 t/s and llama.cpp at 43.7 t/s. README describes the weekly cron.
- [x] 5. `make openspec-validate NAME=weekly-registry-sync` exits 0 and `make test-unit` exits 0 with every task in this file checked.
- [x] 6. `tests/test_registry_sync_trend.py` passes explicit VRAM, RAM, and architecture into `rank_models`, `rank_engines`, `weight_budget_gb`, and `strata_choice` for the October 5 fixture and the live download.
- [x] 7. `tests/fixtures/trend-list-matrix.json` is the vendored trending list for every (arch, vram, ram) in the grid. `tests/test_trend_list_matrix.py` compares `matrix()` to it. The weekly job rewrites and commits it. `make check-trend-list-matrix` exits 0.
