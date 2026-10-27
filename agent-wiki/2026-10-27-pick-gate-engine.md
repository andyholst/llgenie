# 2026-10-27 — the pick gates on the measured minimum, and the suite asserts rules

Implements #669 (task part) with #693's de-pinning, and carries the fix for #730.

## What was verified against the spec

- **The gate.** `fits()` reads `vram_min`, falling back to `vram_tier`. Measured on the
  2026-10-27 store at a 16 GB card: in all 8 rows where the two disagree, the README's VRAM
  column agrees with `vram_min` and never with the tier (`Qwen3.8-27B`: min 12 GB, tier
  16 GB; a 9B row: min 32 GB, tier 16 GB). Before the change the list offered the 32 GB
  model and hid the 12 GB one.
- **The printed list matches the gate.** `llgenie --trend` passes `ram_gb`, so a model above
  `system_ram_min` is not printed as servable.
- **The suite on the synced store** (`generated_utc=2026-10-27`, 112 models): acceptance 83
  passed (was 32 failed), arch_perms 74 (was 21), trend_pick 90 (was 12), tensorfold 36 (was
  5), mac 18 (was 4), card_aware 14 (was 1). Zero failures in each.
- **The store is not in the branch.** `git show --name-only` on each commit: no path under
  `data/`. The vendored store lands through the `registry-sync` PR.

## Decisions

- **The measurement is the gate, not the label.** `vram_tier` is the README's display bucket;
  gating on it made the trend list contradict the column the user reads in the same table.
- **Spelling is not identity** (#730). `_canon_format` compared names exactly, so upstream's
  `LiteRT-LM` read as display text: the normaliser dropped a real format and restated GGUF
  for `google/gemma-4-E2B`, which serves no GGUF. The key is now letters+digits, so
  `LiteRT-LM` → `litertlm`; the vocabulary is unchanged, so `Ornith 1.5` and `LLM (MoE)` are
  still dropped.
- **A rule, never a row.** Every de-pinned test derives its expectation from `mp.fits()`,
  `offer()` or the store's own order. The VRAM column is found by header name (the cell is
  now `**12GB**<br><sub>…</sub>`), printed lines are matched POSITIONALLY (a row name is a
  prefix of another row's name), and the TensorFold seams compute the row the store serves
  and both positions it can be numbered by (`--select N` numbers the pickable list, and
  `--engine` narrows that list).
- **The matrix resolves the host's RAM, not just its card.** `matrix(gb=None)` resolved the
  card from the host but left `ram_gb` at `None`, so `llgenie --matrix` without `--ram`
  ignored the store's `system_ram_min` while `offer()` applied it — measured on the
  synced store: `qwen3.8-27b` (min 12 GB VRAM) listed at `--vram 16` on a 16 GB-RAM host
  whose floor is higher. `matrix()` now resolves RAM the way it resolves the card.
- **A residue is filed, not smoothed.** `test_trending_quant_catalog.py` keeps 2 failures: an
  engine can be offered for a model with no downloadable plan (`bonsai-2-9b`/MLX names only
  unreadable repos; `nemotron-dory-4b/llama.cpp` has a readable repo with no catalogueable
  weight). Generalising the TensorFold-only gate reds 29 fork tests, so the fix is a product
  decision, filed as #731 — not a test to loosen.

## Corrected after the first CI run: the branch is green on the store it SHIPS with

The first push measured every de-pinned file on the locally synced store (112 models) and
never on `main`'s committed one (23 models) — so `linux / unit` came back with 129 failures
(61 matrix fixture, 60 the still-uncommitted `test_pick_full_registry` rewrite, 3
`test_registry_sync_trend`, 2 `test_trend_pick`, 2 acceptance, 1 `test_model_engine_pick`).
The cause was one class of defect, not 129: a test that re-derived "does it fit" from
`vram_tier` instead of calling `mp.fits()`, and a test that froze WHICH of the store's two
VRAM figures the README column prints.

- **`mp.fits()` is the only fit.** `tests/test_model_engine_pick.py` and
  `tests/test_registry_sync_trend.py::_fits_card` restated the gate as
  `_num(vram_tier) <= card_class_gb(gb)`; both now call the product's own decision.
- **The column is a stated figure, not a chosen one.** `vram_min` and the README's VRAM cell
  agree on the 2026-10-27 store and disagree on `main`'s 2026-10-13 one (8 of 23 rows), so
  the parser tests accept EITHER figure and the suite never freezes which one upstream
  prints. Which field the GATE uses is proved hermetically in
  `tests/test_registry_footprint.py::test_the_gate_reads_the_stated_minimum_not_the_display_tier`
  (both directions, no store involved) — a data-agreement test can only ever prove today's
  numbers, and this suite has to survive the sync.
- **The frozen October-5 expectation is derived** from the fixture through `mp.fits()`
  instead of a literal name list.
- **The matrix fixture is regenerated** from the committed store
  (`make render-trend-list-matrix`, 81 cases) — the branch had left the pre-#669 copy.
- **Every spec `- **Test:**` reference resolves.** One scenario named
  `test_225_acceptance_strata_on_a_16gb_card`, which does not exist in this branch or on
  `main`; it now names `test_ac1_rows_are_the_readme_models_that_fit_in_readme_order`, the
  test that actually builds its expectation from `mp.fits()` (checked programmatically: 9
  references, 0 missing).

## Status

PR **#732** (base `asimov-agent/llgenie:main`, head `andyholst:feat/pick-gate-engine`) —
`closes #730`; #669/#693 are named as partially addressed there, with #731 and #673 filed as
their own work items. `make openspec-validate NAME=pick-gate-engine` valid, `make check-docs`
ok, `make lint` OK. `test_pick_full_registry.py`'s static goldens are replaced by derived
rules (a static model→filename table is the same snapshot problem); its residue is reported on
the PR, never hidden by a loosened assert.
