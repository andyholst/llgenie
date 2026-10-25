# The engine row decides through the product function, with its cell's identity

## Why

`engine-build` run `40215905868` (head `65c986f`) came back with **4 of its rows red** — `mlx/cuda`,
`tensorrt-llm/cuda`, `vllm/cuda`, `vllm/rocm` — and every one of them is a cell that `DEVICE_ONLY`
already names, with its measured reason, precisely because its CLI cannot import without a device:

```
E       AssertionError: tensorrt-llm/cuda binary trtllm-serve failed the flag check:
E         --help: documented but did not answer (exit 1, 1248 byte(s) of output)
E             ImportError: libcuda.so.1: cannot open shared object file: No such file or directory
E         every probed flag failed and / is NOT on the device-only exemption list: a binary that cannot
E         answer one flag on this runner proves nothing (add it to DEVICE_ONLY with a reason, or DISABLE
E         the cell — issue #625)
```

Read the third line: **`and / is NOT on the device-only exemption list`**. The slash is an empty engine
and an empty variant — the decider was asked about `("", "")`.

The cause is a second implementation of one stage. `tests/test_engine_version.py` re-runs the probe the
rown already has, and then calls the decider without the cell:

```python
verdict = ei.decide(documented, verdicts, policy)        # tests/test_engine_version.py:73
```

while the product path (`scripts/engine_image.py::binary_file_works`, line 572) calls

```python
decide(documented, verdicts, policy, engine=spec["id"], variant=spec["variant"])
```

So `DEVICE_ONLY.get((engine, variant))` can never match on the pytest path: #625's exemption is
unreachable from the only job that needs it, and #625's tightening (correctly) turned those four rows red.
The unit suite could not see it either — `tests/test_engine_binary_flags.py` drives `decide()` directly,
WITH the identity, so it tested the decider and never the caller that omits it.

## What Changes

- **`tests/test_engine_version.py`** — the flag case calls `engine_image.binary_file_works(spec)` (the
  function `make test-engine-image` already uses) and asserts its exit status, instead of building its own
  `docker run … BINARY_PROBE` and its own `parse_probe`/`decide` chain. One code path decides every row, so
  there is no second call site that can forget the cell identity; the per-flag table the function prints is
  the row's evidence, and the `DEVICE_ONLY` exemption applies exactly as it does for the CLI.
- **`tests/test_engine_binary_flags.py`** — a regression test that keeps the duplication from coming back:
  the engine-row test may not carry a `BINARY_PROBE`/`decide(` call of its own, and (driven through the real
  `binaries.json` manifest) every `DEVICE_ONLY` cell is accepted with its own identity and red with an
  empty one — the shape the bug had.
- **`README.md`** — says which function decides an engine row, so a reader adding a cell knows there is one
  path and where the exemption is applied.

## Impact

- The four cells go green for the right reason: the file must exist in the image, the flags a user types are
  still probed and tabulated, and the version is proven by the image's own `detect` entrypoint — which is
  what `DEVICE_ONLY` documents per cell.
- A future cell that answers nothing without a device is still RED unless it is added to `DEVICE_ONLY` with
  a measured reason, and the failure now names the cell instead of `/`.
- No product behaviour changes: `scripts/engine_image.py` is untouched.
