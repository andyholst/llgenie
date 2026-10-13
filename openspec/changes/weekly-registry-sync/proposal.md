# weekly-registry-sync — proposal

Issue: [#179](https://github.com/asimov-agent/llgenie/issues/179)

## Why

`llgenie` with no model prints the vendored trending list (`data/models.json` plus
`data/trending-README.md`) and, for the model you pick, the inference server with
the highest t/s that this host can run. It does not fetch that list at startup.

The vendored copy is `generated_utc=2026-10-05T23:49:35Z` (14 models). Upstream
`andyholst/trending-local-llms` is newer (22 models on 2026-10-12, including
models whose README VRAM column is at most 48 GB). `registry-sync` is supposed
to copy that file and open `chore/registry-sync`. The scheduled runs fail in
`sync` before the pull request step. Run
[38253687834](https://github.com/asimov-agent/llgenie/actions/runs/38253687834)
is the latest failure. `make sync-registry` and `make check-registry` succeed.
`make skills-validate REGISTRY=data/models.json` then exits 1 because upstream
`engines{}` names servers llgenie does not ship (`mlx-serve`, `oMLX`,
`ExLlamaV3`, `MegaCapybara`, `omlx-exl3`, `llama.cpp (LlamAmpere fork)`,
`glm-flash-lite`). `scripts/engine_skills.py` `validate()` reports every such
name as an error. The pull request is never opened, so the startup list stays
on the October 5 measurements.

On that stale list a 48 GB CUDA host is offered Qwen3.8-27B on SGLang at 44 t/s.
The current upstream registry, ranked by the same `rank_engines` path, offers
that model on vLLM at 300 t/s (a CUDA figure on an engine llgenie already
ships). MegaCapybara's 500 t/s row is higher and is not offered: there is no
skill and no image. Qwen3.8-Flash-Next's skilled CUDA figure moves from Strata
124 t/s to Strata 140 t/s. Models over 48 GB (Cyber-Frost 3.8 MLX, 128 GB) stay
out of a 48 GB card's list.

## What Changes

- `registry-sync` runs weekly, cron `17 5 * * 1`, still separate from
  `engine-bump` (`23 6 * * 1`). `workflow_dispatch` still runs it once.
- The sync still byte-copies upstream `data/models.json` and `README.md` into
  `data/models.json` and `data/trending-README.md`, then regenerates both quant
  catalog copies. It commits `data/trending-quant-catalog.json` as well as the
  test fixture. It does not add or edit `skills/engines/**`.
- `make skills-validate REGISTRY=data/models.json ALLOW_UNSKILLED=1` (the sync
  job and `make ci-unit`) does not fail when the registry names an engine with
  no skill. The default `make skills-validate` against
  `tests/fixtures/trending-models.json` still fails on that name. A skill whose
  `engine:` is absent from the registry is still an error.
- The startup list is unchanged in shape: README order (buzz plus a log of
  consumer t/s), VRAM column `<=` the card, and `rank_engines` puts the highest
  t/s server this host can run first. An engine with no image is omitted there.
  A higher skilled t/s in the new file becomes that row's recommendation.
- `tests/fixtures/trend-list-matrix.json` is that list for every
  `cuda|rocm|vulkan|metal|cpu` card at 8, 16, 24, and 48 GB and RAM at 8, 32,
  60, and 64 GB, plus a 15.99 GiB CUDA card. It is `matrix(registry, vram, ram, arch)`,
  the call `llgenie --matrix --vram --ram --arch` makes. The weekly job
  rewrites it with `make render-trend-list-matrix` and commits it. A registry
  change that leaves the fixture stale fails `make check-trend-list-matrix`
  and `tests/test_trend_list_matrix.py`. The pull-request diff of the fixture
  is the new list.
- `tests/fixtures/registry-before/` is the 2026-10-05 `models.json` and README.
  `tests/test_registry_sync_trend.py` syncs the live upstream with
  `sync_registry.sync` and compares `rank_models` / `rank_engines` before and
  after for a 48 GB CUDA card. The same test passes card size, system RAM, and
  architecture (cuda, rocm, vulkan, metal, cpu) into those functions and into
  `weight_budget_gb` / `strata_choice`. Pins in `tests/test_trend_pick.py` that
  named the October 5 engines follow the vendored file, so a later sync is not
  rejected for quoting SGLang at 44 t/s or llama.cpp at 43.7 t/s.

## Out of scope

Adding skills or images for `mlx-serve`, `oMLX`, `ExLlamaV3`, `MegaCapybara`,
`omlx-exl3`, the LlamAmpere fork, or `glm-flash-lite`. Reordering the model
list away from the README "Most loved" order. Merging the sync pull request.
