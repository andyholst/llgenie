# 2026-10-13 weekly registry sync (issue #179)

The startup list is the vendored `data/models.json` (2026-10-05, 14 models).
Upstream on 2026-10-12 has 22 models. `registry-sync` downloaded that file and
then `skills-validate` exited 1 on seven engines with no skill, so
`chore/registry-sync` was never opened. Latest red run: 38253687834.

`rank_engines` already drops those engines. On the live file a 48 GB CUDA card
ranks Qwen3.8-27B on vLLM at 300 t/s; the October 5 file ranks it on SGLang at
44 t/s. MegaCapybara at 500 t/s has no skill and is not offered.

The sync cron is weekly `17 5 * * 1`. `ALLOW_UNSKILLED=1` is the sync and
`ci-unit` check of `data/models.json`. The pinned skill fixture stays strict.
`tests/fixtures/registry-before/` is the October 5 snapshot.
`tests/test_registry_sync_trend.py` downloads the live registry with
`sync_registry.sync` and compares `rank_models` before and after. The same
file passes card size, system RAM, and architecture into `rank_models`,
`rank_engines`, `weight_budget_gb`, and `strata_choice`.
`tests/fixtures/trend-list-matrix.json` is `matrix(vram, ram, arch)` for the
vendored registry. The weekly job rewrites it; a stale copy fails
`tests/test_trend_list_matrix.py`.
