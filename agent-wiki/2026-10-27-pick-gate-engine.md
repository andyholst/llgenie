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
- **A residue is filed, not smoothed.** `test_trending_quant_catalog.py` keeps 2 failures: an
  engine can be offered for a model with no downloadable plan (`bonsai-2-9b`/MLX names only
  unreadable repos; `nemotron-dory-4b/llama.cpp` has a readable repo with no catalogueable
  weight). Generalising the TensorFold-only gate reds 29 fork tests, so the fix is a product
  decision, filed as #731 — not a test to loosen.

## Status

Branch `feat/pick-gate-engine` (4 commits) pushed to the fork. Not yet a PR: `make test-unit`
as a whole still reds on the goldens in `test_pick_full_registry.py` (~24) and `#673`'s three
engine-skill-gap cases.
