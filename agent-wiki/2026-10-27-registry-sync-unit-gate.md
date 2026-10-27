# The weekly sync's own `test-unit` gate passes on the store it just downloaded

Issue #750 (the run-failure reactor's filing for the `registry-sync` run at `d190aed`), which is the
same work as the store review #749. Delivered in the branch's PR.

## What was wrong

The sync job downloads the store, regenerates every derived table, then runs `make test-unit` before
it opens its PR. Since the 2026-10-13 store that step has been red, so no sync PR was ever opened and
`main` ranked from a 13-day-old registry (23 models / 24 engines) while upstream published 112 / 42.

Reproduced on `origin/main` (`930900b`) in the job's own order: `36 failed, 14486 passed`. Five
families, and only one of them is really "the data changed":

- 21 × `test_pick_matrix_arch_perms.py` — a hermetic file that stubs the Hub and the engine registry,
  but answered a stub model id (`qwen3-8b`) from the REAL committed quant table, so a cuda cell's
  `use_format` became `safetensors`.
- 5 × the CLI-vs-matrix cases — the table carried a `vLLM` cell planned from an MLX-converted repo
  (`qwen3-4b`) and a `Strata` cell pointing at another model's 61.9 GB pack.
- 3 × gated links — `google/gemma-3-1b-it` answers 401, and the live probe called the file missing.
- 1 × the trend-list matrix — a row `matrix()` never considered (8 GB RAM, `system_ram_min` floor)
  printed with an empty server AND an empty reason.
- 6 × engines and catalog coverage — 18 engines the store now names with no skill and no dated
  decision, plus two models whose cell the generator could not derive.

## Decisions taken

- **The generator applies the resolver's own rule.** `plan_download()` already refuses an MLX-named
  repo for `safetensors` (and the reverse); the generator now does the same, and a Strata cell exists
  only for the family `strata_serves()` names. The table stopped inventing downloads.
- **An engine with no plan is not offered.** `rank_engines` gates on the table for a model the table
  covers; a model it does not cover keeps live resolution, so a store synced one step before its
  catalog is still served. This is the catalog clause of #731 — the wider "for every engine, always"
  generalisation (and its 29-test blast radius) stays #731's own change.
- **A gated link is not a dead one.** The live probe now classifies 401/403 as `gated` (file exists,
  this credential may not read it), which is the rule `web-coverage` and the catalog generator already
  apply (#418).
- **The two catalog-coverage rules are stated on `offer()`**, the path that decides what `llgenie`
  prints, not on the raw rank list.
- **18 engines decided, not skipped.** Each entry in `data/unsupported-engines.json` is dated, reasoned
  from the project's own README, and names the upstream it was read from: three llama.cpp forks
  (KV-streaming, hikicoder, strix-llama.cpp) are explicitly `not-shipped`, the rest `deferred` because
  they are a desktop app, a per-chip or per-box experiment, a datacenter stack, or a library with no
  first-party server.

## Verified

- `make test-unit` on the synced store: **14527 passed, 6 deselected in 1419.57s** (the step the sync
  job reds on; it was `36 failed, 14486 passed` before this change).
- The families separately, in the test image: the pick suite, the catalog file, the trend-list matrix
  and the hub probe all green.
- `make test-strata-live` (kept out of the hermetic gate): `31 passed`. Its
  `test_the_registry_model_is_the_one_strata_serves` pinned "exactly one store row is Strata's model";
  the new store carries six per-box rows of that same base model, so the test now asserts the rule —
  every row `strata_serves()` accepts IS that family's base model — instead of a row count.
- `make check-engine-skill-gap`: `42 engines, 16 skills; shipped 16 (4 with no image),
  known-unsupported 26, unresolved 0`.
- The regenerated artifacts carry the same stamp (`generated_utc` `2026-10-27T12:53:42Z`).
- Spec scenarios and their tests: `openspec/changes/fix-registry-sync-unit-gate/specs/registry-sync-gate/spec.md`.

## Not covered

- The `rank_engines` generalisation for a model the table does not cover — #731, filed with its own
  measured evidence.
- Building an image for any of the 18 engines a future decision promotes — each is its own work item
  under the "a real OpenAI server always gets an image" rule.
