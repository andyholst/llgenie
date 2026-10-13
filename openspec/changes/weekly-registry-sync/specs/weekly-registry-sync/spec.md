# weekly-registry-sync

## ADDED Requirements

### Requirement: the trending registry syncs weekly without failing on an engine llgenie does not ship
`registry-sync` MUST run on cron `17 5 * * 1` and on `workflow_dispatch`. That
cron MUST stay distinct from `engine-bump` (`23 6 * * 1`). The job MUST
byte-copy upstream `data/models.json` and `README.md` into `data/models.json`
and `data/trending-README.md`, regenerate `data/trending-quant-catalog.json`
and `tests/fixtures/trending-quant-catalog.json`, and open or update
`chore/registry-sync` with `secrets.BUMP_TOKEN` when those files differ from
`main`. The job MUST NOT merge and MUST NOT change `skills/engines/**`.

`engine_skills.validate` MUST still report a registry engine that has no skill.
The sync job and `make ci-unit`'s check of `data/models.json` MUST pass
`ALLOW_UNSKILLED=1`, and that mode MUST NOT report those names. A skill whose
`engine:` is not a registry key MUST still be an error in that mode. The
default `make skills-validate` against `tests/fixtures/trending-models.json`
MUST stay strict.

WHEN the weekly job finds a newer upstream registry
THEN it opens one pull request and an engine with no skill is omitted from the
trend offer rather than failing the job.

#### Scenario: the workflow is weekly and opens a pull request with the owner token
- **Given** `.github/workflows/registry-sync.yml`
- **When** its schedule, its validate step, and its pull-request step are read
- **Then** the cron is `17 5 * * 1`, the validate step passes `ALLOW_UNSKILLED=1`, and the pull request uses `secrets.BUMP_TOKEN`
- **And** the committed paths are `data/models.json`, `data/trending-README.md`, `data/trending-quant-catalog.json`, `tests/fixtures/trending-quant-catalog.json`, and `tests/fixtures/trend-list-matrix.json`
- **And** the job rewrites that trend-list matrix with `make render-trend-list-matrix` before it commits
- **And** the workflow does not merge and does not add a file under `skills/`
- **Test:** `tests/test_registry_sync_trend.py::test_registry_sync_workflow_is_weekly_and_allows_unskilled_engines`

#### Scenario: an engine with no skill fails a strict validate and not the sync validate
- **Given** the 2026-10-05 registry fixture plus an engine no skill covers
- **When** `validate` runs with and without `allow_unskilled`
- **Then** the strict run names that engine as having no skill, and the sync run does not
- **And** removing a skill's engine from the registry is still an error when unskilled engines are allowed
- **Test:** `tests/test_registry_sync_trend.py::test_allow_unskilled_omits_unknown_engines_and_still_requires_our_skills`

### Requirement: a live sync adopts a higher skilled t/s for a model that fits 48 GB
The trend offer for a card MUST be `rank_models` on the registry that
`sync_registry.sync` wrote: README order, `vram_tier` at most the card size,
and each model's engines from `rank_engines` (highest t/s on this host's
hardware first). A model whose `vram_tier` is above 48 GB MUST be absent from
the 48 GB list. An engine name with no llgenie image MUST be absent from that
ranking.

`tests/fixtures/registry-before/models.json` and `README.md` MUST stay the
vendored snapshot `generated_utc=2026-10-05T23:49:35Z`. The acceptance test
MUST download the live upstream with `sync_registry.sync` (no stand-in for
that download) and rank both files with `rank_models` and `rank_engines`.

WHEN the live registry raises the best same-hardware t/s of a model on an
engine llgenie can run
THEN the 48 GB CUDA ranking for that model uses the new engine and the higher
t/s, and the October 5 ranking still shows the old engine and the old t/s.

#### Scenario: the October 5 list and the downloaded list differ by a higher t/s
- **Given** the frozen 2026-10-05 models and README
- **When** `sync_registry.sync` downloads the live upstream into a temp directory and both registries are ranked for CUDA at 48 GB
- **Then** the download is newer, matches its README order, and includes models the October 5 file does not that still fit 48 GB
- **And** every model whose VRAM column is above 48 GB is outside that list
- **And** at least one model, including Qwen3.8-27B, has a higher same-hardware t/s on an engine llgenie ships, and `rank_engines` returns that engine and that t/s
- **And** an upstream engine with no skill is absent from the ranking even when its raw t/s is higher
- **Test:** `tests/test_registry_sync_trend.py::test_live_sync_adopts_a_higher_skilled_tps_for_models_that_fit_48gb`

#### Scenario: the October 5 CUDA list is the frozen fixture, not a hard pin on the vendored file
- **Given** the frozen 2026-10-05 registry
- **When** it is ranked for a 16 GB CUDA card
- **Then** the servable names are the October 5 README rows at or under 16 GB, Qwen3.8-27B's top engine is SGLang, and Qwen3.8-Flash-Next's top engine is Strata
- **Test:** `tests/test_registry_sync_trend.py::test_october_5_fixture_ranks_qwen38_27b_on_sglang`

#### Scenario: VRAM, RAM, and architecture are inputs to the real rank and budget
- **Given** the frozen 2026-10-05 registry and the downloaded live registry
- **When** `rank_models` and `rank_engines` run with an explicit card size and architecture, and `weight_budget_gb` and `strata_choice` run with an explicit RAM size
- **Then** a model whose VRAM column is above that card is absent, and the first engine is the highest t/s engine that has an image for that architecture
- **And** CUDA, ROCm, Vulkan, Metal, and CPU do not share one engine choice for Qwen3.8-27B on the October 5 file
- **And** a 15.99 GiB card still counts as 16 GB
- **And** MoE download budget on CUDA grows with RAM, Metal and CPU budgets do not, and Strata's quant switches to IQ3_XXS at 60 GB of RAM
- **And** on the live file the CUDA same-hardware t/s for Qwen3.8-27B stays above the October 5 figure at 16 GB and at 48 GB
- **Test:** `tests/test_registry_sync_trend.py::test_rank_follows_the_given_vram_ram_and_arch`

### Requirement: the vendored trending list is pinned per architecture, VRAM, and RAM
`tests/fixtures/trend-list-matrix.json` MUST be the output of `matrix(registry, vram, ram, arch)` on the vendored `data/models.json` for every architecture `cuda`, `rocm`, `vulkan`, `metal`, and `cpu`, every card size 8, 16, 24, and 48 GB, every RAM size 8, 32, 60, and 64 GB, and a 15.9921875 GiB CUDA card with 62 GB of RAM. Each case MUST list the README models whose VRAM column fits that card, in that README order (buzz plus log2 of consumer t/s). The server on a row MUST be the first engine `matrix` returns for that architecture. A model that fits the card and has no quant that fits the RAM MUST stay in the list with the reason `matrix` reports. `generated_utc` on the fixture MUST equal `data/models.json`.

The weekly job MUST rewrite this fixture with `make render-trend-list-matrix` after the quant catalog and MUST commit it with the registry. `make check-trend-list-matrix` and `tests/test_trend_list_matrix.py` MUST fail when the fixture differs from a fresh `matrix()` call.

WHEN the vendored registry changes and the fixture is not rewritten
THEN the unit test for that (arch, vram, ram) fails, naming the case.

#### Scenario: each arch, vram, and ram has the committed trending list
- **Given** the vendored registry and `tests/fixtures/trend-list-matrix.json`
- **When** `matrix(registry, vram, ram, arch)` runs for one case in the grid
- **Then** its models and servers equal the committed rows for that case, in README order
- **And** the fixture's cases are exactly the grid, and its `generated_utc` is the vendored registry's
- **And** the CUDA 16 GB list serves its first model on Strata at 64 GB of RAM and records a reason at 8 GB of RAM
- **Test:** `tests/test_trend_list_matrix.py::test_trend_list_matches_the_committed_matrix`
- **Test:** `tests/test_trend_list_matrix.py::test_the_committed_matrix_is_the_vram_ram_arch_grid`
- **Test:** `tests/test_trend_list_matrix.py::test_ram_changes_which_cuda_16gb_model_is_served`
