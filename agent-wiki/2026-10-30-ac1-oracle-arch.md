# The AC1 oracle must pass the `arch` the product passes (PR #935, issue #669)

Review finding at PR #935 head `82e105dd`. The branch added an `arch` parameter to
`model_engine_pick.fits()` and used it to exclude Apple/Metal "unified memory" runs on a
non-Metal host (`scripts/model_engine_pick.py`, `apple_excluded = arch is not None and arch
not in ("metal","mlx","apple")`), and it rewrote the AC1 acceptance oracle in
`tests/test_trend_list_acceptance.py`. The rewrite calls `mp.fits(m, gb, ram)` **without**
`arch`, so `arch=None` counts the very runs the product drops, and 8 of 12 backends red while
the product is right.

Measured at the head (gguf venv `~/llama-gguf-tools/.venv/bin/python`):

- cpu/16gb: `offer()` rows 65, `fits(no arch)` 67, `fits(arch=backend)` 65
- cuda/24gb: 81 / 82 / 81; vulkan/16gb: 65 / 67 / 65
- the gap is exactly `Bonsai 2 27B on M4 Max` and `Qwen3.6 27B` (Apple/Metal-only runs)
- `pytest tests/test_trend_list_acceptance.py -k ac1_rows_are_the_readme` → 8 failed, 4 passed
- on `live/main 564e9383` the same 12 pass — main's `fits()` has no `arch` parameter yet

The fix is one token — pass `backend`, as `offer()` does:

```
fit = {m["name"]: m for m in reg["models"] if mp.fits(m, gb, ram, backend)}
```

Applied and executed: 12 passed in 0.86s, then the pristine file restored. The test file is
neither excluded nor deselected in `tests/fixtures/unit-suite.json`, so `ci-unit`'s
`test-unit` runs it and the unit leg reds on it.

Spec / issue / PR: issue #669; PR #935.
