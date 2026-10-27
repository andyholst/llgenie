# A `formats` name that is not a format is not data the guard can lose

## Why

#692 made the sync normalise the store on the way in: `normalise_formats` drops a `formats[].name`
outside `FORMAT_VOCAB = (GGUF, MLX, safetensors, mlx-safetensors, litertlm)` — upstream writes model
and recipe text there ("Qwen3.8-Flash-Next 125B", "Ornith 1.5") — and states the real format instead
(83 rows on the 2026-10-26 store).

The additive-only guard reads every dropped `formats` name as a loss, so the FIRST normalised sync reds
`make check-registry-keys` (issue #698, measured on `main` @ `0aeb77c`, in the job's order):

```
make sync-registry       # OK: 23 -> 106 models (2026-10-26T14:06:43Z) (+contract)
make check-registry      # OK … contract satisfied, README order matches, links answer
make check-registry-keys # exit 1
  LOSS: qwen3.8-flash-next-125b: formats lost ['Qwen3.8-Flash-Next 125B']
  LOSS: glm-5.3-flash: formats lost ['GLM-5.3-Flash']
  … 10 in total …
  FAILED: 10 loss(es) vs HEAD:data/models.json
```

The guard is right to fail on a *format* that disappears. A display name that is not a format was never
data: dropping it removes nothing a consumer can rank or download, which is the same reasoning #668
applied to the derived `engagement.seen_posts` placeholder.

## What changes

`_real_formats(row)` returns only the `formats[].name` values that are in `FORMAT_VOCAB` (compared
case-insensitively, returned in the vocabulary's canonical spelling), and the loss check becomes a set
difference over those:

```
lost_formats = sorted(_real_formats(pm) - _real_formats(cm))
```

`FORMAT_VOCAB` is imported from `scripts/sync_registry.py` — the module that drops the names — so the two
rules cannot drift apart: widening the vocabulary widens the guard in the same edit.

## Impact

- `scripts/registry_keys.py` — `FORMAT_VOCAB` import and `_real_formats()`, used for the `formats` check.
- `tests/test_registry_keys.py` — a non-format name dropped is not a finding; a real format dropped still
  is (both directions, over the real `compare()`).
- `data/models.json` is untouched: the guard is what changes, never the store.

Verified on the real store: after `make sync-registry` on `main` @ `0aeb77c`, `make check-registry-keys`
reports `OK: additive only … (106 models, 81 note(s))` where it reported 10 LOSS findings before.

Not in this change: the 101 data-pinned tests (#677), the 16 engines with no skill or dated decision
(#673), and the contract #694 vendors (PR #699).
