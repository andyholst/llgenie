# The vendored registry is normalised on the way in (issue #687)

## Why

Upstream's `data/models.json` grew 23 → 106 rows and stopped writing formats in `formats[].name`:
it now repeats the model or a recipe there (`"Qwen3.8-27B"`, `"LLM (MoE)"`, `"Bonsai 2 27B
(mlx.fast)"`). llgenie resolves a download per format, so on that store `model_engine_pick` cannot
map most rows to a plan: the matrix yields `use_format: safetensors` where a cuda cell needs a GGUF,
the planner raises `StopIteration`, and the sync job's own `make test-unit` step reds 101 hermetic
tests (`14369 passed`) — so the weekly PR cannot land (measured in #687, on the real store).

The vendored copy was "verbatim": the repo took upstream's file as-is and the guard only checked that
nothing was *lost*. Nothing was lost — the store now contains a different *shape*, which no loss
guard can see.

## What changes

1. **`scripts/sync_registry.normalise()`** runs at vendor time, before the file is written:
   - `formats` restricted to the vocabulary (`GGUF | MLX | safetensors | mlx-safetensors |
     litertlm`), canonical spelling, duplicates collapsed;
   - a format name outside the vocabulary is dropped, and a row left with none **states the format
     its own repo/id names** (`-GGUF` → GGUF, `mlx` → MLX, `litertlm` → litertlm), else GGUF — the
     picker's documented "most-downloaded `<name>-GGUF` repo" fallback, applied once at vendor time
     so the file says what llgenie does;
   - a duplicated row id is dropped.
   Every departure prints a note, and the sync log / PR body show them.
2. **Rows are not folded.** Upstream's rows are distinct entities (a base model, a merged finetune,
   an MLX conversion, a run on one box) and its README lists each as its own row; a name heuristic
   cannot separate `Qwen3.8-27B Defiance Uncensored` from `Qwen3.8-27B (iPad Pro + eGPU R9700)`, and
   folding dropped real models (measured: 28 rows folded, the fold merged different finetunes). The
   vendored README stays upstream's list, verbatim, and the store keeps one row per upstream row.
3. **`AGENTS.md`, `README.md`, `docs/BOTS.md`** record the departure from "verbatim" — what is
   normalised, what is not, and why folding is refused.
4. **`tests/test_registry_normalise.py`** locks each rule against real JSON (junk format restated from
   the repo, MLX row kept MLX, canonical dedupe, distinct rows kept, duplicate id dropped, and a real
   `sync()` writing a normalised store that `validate()` accepts).

## Impact

- `scripts/sync_registry.py` — `FORMAT_VOCAB`, `_canon_format`, `_format_from_repo`,
  `normalise_formats`, `normalise`, and `sync()` writing the normalised store.
- `AGENTS.md` (vendored-registry rule), `README.md` (the two "verbatim" claims), `docs/BOTS.md`.
- `tests/test_registry_normalise.py` — new, in `make test-unit` by discovery.

## Not covered

The remaining 52 failures in the trend/pick tests are **data-pinned assertions and the README's new
VRAM cell** (`**16GB**<br><sub>stated by the source …</sub>` breaks `test_trend_pick`'s cell parser) —
a test-suite change of its own, tracked in #687 with the measurements.
