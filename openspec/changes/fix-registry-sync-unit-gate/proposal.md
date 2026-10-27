# The weekly sync's own gate passes on the store it just downloaded

## Why

`registry-sync` failed on every run since the 2026-10-13 store (issue #750): the job downloads the
upstream store, regenerates every derived table, and then its own `make test-unit` step reds, so
`Open / update the sync PR` never runs and `main` has been ranking from a 13-day-old registry
(23 models, 24 engines) while upstream publishes 112 models and 42 engines.

Reproduced in a worktree in the job's own order (`origin/main` at `930900b`):

```
make sync-registry            # 23 -> 112 models, generated_utc 2026-10-27T12:53:42Z
make sync-quant-catalog       # 90 models, 1656 links (3 gated)
make render-trend-list-matrix # 81 cases
make render-engine-skill-gap  # wrote data/engine-skill-gap.json
make test-unit                # 36 failed, 14486 passed
```

The 36 are 5 families, and only one of them is the store's own data:

| n | family | what it actually is |
|---|---|---|
| 21 | `test_pick_matrix_arch_perms.py` | a hermetic stub file reading the REAL committed HF class table for a stub id (`qwen3-8b`) that upstream now also lists |
| 5 | `test_pick_full_registry.py` (CLI vs matrix) | the catalog offered a `vLLM` cell whose plan is an MLX repo, and a `Strata` cell pointing at a different model's weights |
| 3 | `test_pick_full_registry.py` (gated links) | a gated repo (`google/gemma-3-1b-it`) reported as a missing file |
| 1 | `test_trend_list_matrix.py` | a row `matrix()` never considered (the 8 GB RAM list) printed with no server and no reason |
| 3+2 | `test_engine_skill_gap.py`, `test_trending_quant_catalog.py` | 18 engines the store now names with no skill and no dated decision, plus two models whose catalog cell the generator could not derive |

## What changes

1. **The generator stops inventing plans** (`scripts/gen_trending_quant_catalog.py`): a
   `mlx-safetensors` / `safetensors` cell is planned only from a repo whose NAME matches the format —
   the rule `model_engine_pick.plan_download()` already applies — and a Strata cell exists only for the
   model family Strata actually serves (`strata_serves`). Before: `qwen3-4b` got a `vLLM` cell pointing
   at an MLX repo, and every model Strata was measured on got a cell pointing at the 61.9 GB
   Qwen3.8-Flash-Next pack.
2. **The trend-list renderer asks the same question `matrix()` asks** (`scripts/trend_list_matrix.py`):
   the row set is `trend_list(registry, vram, ram)`, so a model the store's `system_ram_min` floor keeps
   out of a low-RAM host is not printed with an empty server and an empty reason.
3. **The live-Hub probe knows a gated link from a dead one** (`tests/hub_probe.py`): 401/403 means the
   file exists and this credential may not read it — the rule this repository already applies in
   `web-coverage` and in the catalog generator (#418).
4. **A hermetic pick test resolves its own stubs** (`tests/test_pick_matrix_arch_perms.py`): the file
   stubs the Hub AND the engine registry, so it also disables the committed catalog, instead of
   answering a stub model from real data.
5. **The 18 engines the store now lists are decided** (`data/unsupported-engines.json`): each entry is
   dated, reasoned from the project's own README, and named with its upstream URL — the rule #229 exists
   for. They are not silently carried: `make check-engine-skill-gap` refuses an engine with neither a
   skill nor a decision.

## Impact

- `scripts/gen_trending_quant_catalog.py`, `scripts/trend_list_matrix.py`, `tests/hub_probe.py`,
  `tests/test_hub_probe.py`, `tests/test_pick_matrix_arch_perms.py`, `tests/test_trend_list_matrix.py`,
  `data/unsupported-engines.json`.
- Regenerated artifacts in the same change: `data/models.json`, `data/trending-README.md`,
  `data/trending-quant-catalog.json` + its fixture, `tests/fixtures/trend-list-matrix.json`,
  `data/engine-skill-gap.json`.
- `agent-wiki/` note + `CHANGES.md` row; README's registry-sync section states what the gate fixes.

Not in this change: the two remaining "an engine is offered for a model whose plan cannot be
downloaded" cases (#731 — the general plan gate, filed with its own evidence), and building images for
any of the 18 engines that a future decision promotes (each is its own work item per AGENTS.md).
