# 2026-10-26 — the vendored registry is normalised on the way in

Implements issue #687 (OpenSpec change `registry-normalise-on-vendor`), the option chosen there:
normalise the store on the way in rather than accept upstream's shape as-is.

## What was wrong (measured)

Upstream's store grew 23 → 106 rows and writes model/recipe names into `formats[].name`
(`"Qwen3.8-27B"`, `"LLM (MoE)"`, `"Bonsai 2 27B (mlx.fast)"`). llgenie resolves a download per
format, so on that store `model_engine_pick` yields `use_format: safetensors` where a cuda cell
needs a GGUF and the planner raises `StopIteration`; the sync job's own `make test-unit` step reds
101 hermetic tests, so no sync PR can land. The additive-only guard cannot see it: nothing was lost,
the store's *shape* changed.

## What was decided

- **Formats are normalised at vendor time** (`sync_registry.normalise()`): vocabulary only
  (`GGUF | MLX | safetensors | mlx-safetensors | litertlm`), canonical spelling, duplicates
  collapsed; a non-format name is dropped and a row left with none states the format its own
  repo/id names, else GGUF — the picker's documented `<name>-GGUF` fallback, applied once so the
  vendored file says what llgenie does. A duplicated row id is dropped. Every departure prints.
- **Rows are not folded into "one row per model".** Measured: a name heuristic folds 28 rows and
  merges distinct entities (`Qwen3.8-27B Defiance Uncensored` is a finetune; `Qwen3-1.7B (Woodcock
  on MLX)` is a run of a model upstream lists nowhere else), and upstream's own README lists each as
  its own row. The vendored README stays upstream's list, verbatim.

## Verified

- real store: `make sync-registry` → 106 normalised rows, 83 printed notes; `registry_keys.py`
  exits 0 (additive, 81 drift notes); `make check-registry` passes.
- `tests/test_registry_normalise.py` pins every rule; the full loop gates and the remaining
  test-suite work are tracked in `tasks.md` and #687.

## Status

Implementation complete on `feat/registry-normalise-on-vendor`. Remaining, as #687's second half: the
trend/pick tests' data pins and the README's annotated VRAM cell (`**16GB**<br><sub>…</sub>`), which
still red 52 of them on the new store.
