# registry-guard-measurement-identity — proposal

Issue: [#668](https://github.com/asimov-agent/llgenie/issues/668) — unfreezes [#534](https://github.com/asimov-agent/llgenie/issues/534)

## Why

`make check-registry-keys` (`scripts/registry_keys.py`) is the consumer's additive-only guard on the
vendored `data/models.json`: the weekly `make sync-registry` replaces the file wholesale, so a sync that
LOST a model, key or measurement had to be caught here (#233). It compares each measurement group by the
exact `(engine, hardware)` pair and fails on a lowered t/s or engagement counter.

Measured on 2026-10-26 against upstream `master` (`4eb28c1`, store `2026-10-26T11:56:20Z`):

- llgenie vendors **23 models / 24 engines** from `2026-10-13T14:31:40Z`; upstream holds **106 models /
  40 engines**. The weekly sync has not opened a PR since 2026-10-13.
- The guard reports **47 losses**, and almost none of them is a loss:
  - **18 of 24 "measurement … is gone"** name a `source_post` that is still in the new store — upstream
    only refined the hardware label (`DFlash2 on RTX 6000` → `RTX 6000 24GB`, `Strata on RTX 4090`,
    `oMLX on M4 Max`, …). The remaining 6 posts are in the store too, re-attributed to a split model row
    or demoted to the `engagement.seen_posts` placeholder.
  - **10 "counter lowered"** are live re-scrapes: `DFlash2 on RTX 4090 24GB likes 21 → 4` while its
    comments (3 → 8), reshares (5 → 72) and views (5451 → 12267) rose for the same post.
  - **10 "key 'engagement.seen_posts.*' is gone"** come from one model whose `seen_posts` placeholder
    upstream rebuilt to `[]`; the union of an empty list is an empty set, so every element key read as
    lost.
  - **2 "t/s lowered"**: one is the same relabel (`mlx-serve on M4 Max 146 → 70`, same post, hardware now
    `M4 Max (Apple Silicon, unified memory)`), the other a genuine correction.

So the guard is not doing its job (#534 assumed it was and blamed upstream): it fails the sync on
bookkeeping upstream rewrites in place every refresh, and 13 days of movement — 83 model rows, corrected
figures, the footprint fields of #414 — never reach the trend pick, the matrix or the README list.

## What Changes

- **Measurement identity is the post, not the label.** `scripts/registry_keys.py` now tracks the
  `/status/<id>` of a source post across the WHOLE store (measurements *and* `engagement.seen_posts`), so
  a refined hardware string, a post re-attributed to a split model row, or a row moving between ranked
  and seen-only is the same measurement. A profile link (`https://lightbrd.com/<handle>`) is not a post
  identity at all: upstream upgrades it to the real status URL.
- **The unit that can thin the trend list is the engine.** An engine that had a measurement on a model and
  has none now is a loss (that is exactly what `rank_engines` groups by, and what `matrix()` would lose).
- **A tracked post that is nowhere in the new store is a loss**, whatever model it moved to.
- **The numbers the store RE-READS stop being fatal, and are still printed.** `drift()` returns a
  surviving post's lowered t/s, a decreased engagement counter and a shrunken `seen_posts` placeholder;
  the CLI prints them as `NOTE:` with both numbers and exits 0. A lowered *stated footprint* (model or
  measurement `weight_gb` / `context_tokens` / `system_ram_min`) stays fatal: it is static data about a
  run, not a re-read, and it shrinks the budget llgenie allocates.
- **Everything that was fatal and is a real loss stays fatal**: a model row gone, a key gone from a model
  row, a `backends` / `supported_engines` entry gone, a `formats` name gone, an engine-registry entry
  gone, a footprint lowered.
- **`AGENTS.md`** states the narrowed rule (it currently states the old one), **`README.md`** documents
  what the gate fails on and what it reports, and an **`agent-wiki/`** entry records the work.

Not in this change (each is its own tracked item): the pick semantics that read this data (`vram_tier` vs
`vram_min`, global vs tier-local order, the unvendored `MODEL_CONTRACT.md`) — #669; the matrix grid — #228;
the view filter — #227. Landing the actual 106-model sync is the weekly `registry-sync` job's action once
this gate stops failing it.
