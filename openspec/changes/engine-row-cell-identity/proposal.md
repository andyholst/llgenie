# The engine row decides through the product function instead of a copy of the probe

## Why

`engine-build` run `40215905868` (head `65c986f`) came back with **4 of its rows red** — `mlx/cuda`,
`tensorrt-llm/cuda`, `vllm/cuda`, `vllm/rocm` — and every one of them is a cell that `DEVICE_ONLY`
already names, with its measured reason, because its CLI cannot import without a device:

```
E       AssertionError: tensorrt-llm/cuda binary trtllm-serve failed the flag check:
E         --help: documented but did not answer (exit 1, 1248 byte(s) of output)
E             ImportError: libcuda.so.1: cannot open shared object file: No such file or directory
E         every probed flag failed and / is NOT on the device-only exemption list: a binary that cannot
E         answer one flag on this runner proves nothing (add it to DEVICE_ONLY with a reason, or DISABLE
E         the cell — issue #625)
```

`and / is NOT on …` is the tell: an empty engine and an empty variant, because the pytest row asked the
decider about `("", "")`.

The *symptom* was fixed in flight by #632 (PR #633): that call site now passes `engine=`/`variant=`, and
`decide()` refuses a `policy: device` verdict without them. This change fixes the **cause** — that test is a
second implementation of the row.

`engine_image.binary_file_works(spec)` already does exactly what the test did: it reads the manifest entry,
probes every documented flag plus every flag a user types inside the image, parses the output, decides with
the cell's identity, and prints the per-flag table. The test rebuilt that pipeline by hand instead of
calling it, so the two drifted the moment the decider needed the identity — and only one of them had it.
AGENTS.md forbids a second implementation of one stage for exactly this reason: a copy cannot inherit a fix.

## What Changes

- **`tests/test_engine_version.py`** — the flag case calls `engine_image.binary_file_works(spec)` and asserts
  its exit status, with the captured `[engine-image]` table as the failure evidence. No local `BINARY_PROBE`
  run, no local `parse_probe`, no local `decide`. The row and the CLI now decide through one function, so a
  future change to the decider (the identity, `DEVICE_ONLY`, a new flag family) cannot reach one without the
  other.
- **`tests/test_engine_binary_flags.py`** — a seam test that keeps the copy from coming back: the engine-row
  test's flag case must name `binary_file_works(spec)` and carry no `BINARY_PROBE`/`decide(`/`parse_probe(`
  of its own. (The identity rule itself belongs to #633, and both of its directions are already locked in
  `tests/test_engine_gate_strict.py`; this change deliberately does not duplicate them.)
- **`README.md`** — says which function decides an engine row, and that there is exactly one.

## Impact

- The four cells stop being red for a reason that is not their own: their `DEVICE_ONLY` reason is applied by
  the same code that applies it to every other row.
- A cell that answers nothing without a device is still RED unless it is deliberately named in `DEVICE_ONLY`
  with a measured reason — the check is unchanged, only where its verdict comes from.
- No product behaviour changes: `scripts/engine_image.py` is untouched.
