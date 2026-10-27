# 2026-10-27 — a `formats` name that is not a format is not data the guard can lose

Implements issue #698 (OpenSpec change `registry-keys-format-vocab`).

## What was wrong (measured)

#692 made the sync normalise the store on the way in: `normalise_formats` drops a `formats[].name`
outside `FORMAT_VOCAB` — upstream writes model/recipe text there ("Qwen3.8-Flash-Next 125B",
"Ornith 1.5") — and states the real format instead. The additive-only guard read each dropped name as a
loss, so the first normalised sync reddened `check-registry-keys` before it could ever reach `test-unit`.

A/B on the same freshly synced store (2026-10-26, then 112 rows after upstream moved again):

```
origin/main's registry_keys.py   -> 10 LOSS findings, exit 1
                                 (qwen3.8-flash-next-125b: formats lost ['Qwen3.8-Flash-Next 125B'], …)
this change                      -> [check-registry-keys] OK: additive only (112 models, 82 note(s))
```

## What was decided

`_real_formats(row)` keeps only the `formats[].name` values that are in `FORMAT_VOCAB`, compared
case-insensitively and returned in the vocabulary's canonical spelling; the loss check is a set difference
over those. `FORMAT_VOCAB` is imported from `scripts/sync_registry.py` — the module that drops the names —
so widening the vocabulary widens the guard in the same edit and the two rules cannot drift.

A display name that is not a format was never data: nothing a consumer ranks or downloads disappears with
it. That is the reasoning #668 already applied to the derived `engagement.seen_posts` placeholder. A real
format that goes away (`GGUF` → nothing) is still a LOSS and is still named.

## Verified

- Red first: the new non-format test fails on `origin/main`'s guard (`formats lost ['Model One']`) and
  passes here; the dropped-real-format test passes on both, so the guard keeps its teeth.
- `tests/test_registry_keys.py`: 14 passed.
- Real store, in the job's order: `make sync-registry` → 112 rows; `make check-registry-keys` →
  `OK: additive only — nothing lost (112 models, 82 note(s))`, where `origin/main`'s guard reported 10
  LOSS findings on the same file.
- `make test-unit` and `make openspec-validate NAME=registry-keys-format-vocab` recorded in `tasks.md`.

## Status

Implementation complete on `feat/registry-keys-format-vocab`. `data/models.json` is untouched — the guard
is what changes, never the store. Still open, each its own issue: the 101 data-pinned tests (#677), the 16
engines with no skill or dated decision (#673), and the contract vendoring (#694, PR #699).
