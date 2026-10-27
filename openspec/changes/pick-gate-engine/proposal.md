# The pick gates on the measured minimum, and the suite asserts rules, not rows

## Why

`data/models.json` is the vendored trending-local-llms store, replaced wholesale by the
weekly `registry-sync` PR. The pick suite was written against the 2026-10-13 store (23
models) and pinned what upstream owns: model names, engine names, exact t/s figures, a
golden quant table and the README's row order. On the 2026-10-27 store (112 models, 42
engines) that surfaced as **130 failing tests**, and it hid a product defect behind them:
`fits()` gated on `vram_tier` — the README's *display bucket* — so at a 16 GB card the list
offered models needing 32 GB and hid models needing 12 GB (issue #669).

A suite pinned to data upstream rewrites blocks every sync, and a sync blocked by the suite
is a sync that never lands the data the product ranks from (#693).

## What changes

- `fits()` reads the store's measured `vram_min`, and falls back to `vram_tier` only when the
  store states no minimum. Nothing is invented; the gate is the measurement.
- `llgenie --trend` passes the host's system RAM to `offer()`, so the printed list honours the
  same RAM floor (`system_ram_min`) the rest of the picker applies (#414).
- A `formats[].name` is matched to the format vocabulary by letters and digits only, so
  upstream's `LiteRT-LM` is `litertlm` and not "display text" — which the normaliser used to
  drop, restating GGUF for a repo that serves no GGUF (#730).
- The pick suite asserts RULES: the fitting set comes from `mp.fits()`, the VRAM column is
  found by header name, the README row order is compared to the store's own order, each
  row's own host hardware ranks first, and the TensorFold/MLX/`#1` rows are derived from
  `offer()` and the store — never named, never indexed.
- `make check-quant-catalog` applies the same rule to the table the gate reads
  (`specs/quant-catalog/spec.md`, #736): it fails on a plan the committed table has and the
  generator no longer produces, and only NOTES what the live Hub re-reads (a reorder, a
  newly published conversion) — the `ci-unit` gate was red on `main` itself because the
  `sort=downloads` search returned the same 14 plans in a different order, so no PR could
  reach `test-unit`.

## Out of scope

- Which engines the catalog should carry, and the store's new engine labels that map to no
  llgenie skill — filed as their own issues (#731, #673, #686).
- The vendored store itself: it lands through the `registry-sync` PR, never through this
  change (measured: the branch carries no file under `data/`).
