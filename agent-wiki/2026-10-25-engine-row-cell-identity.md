# 2026-10-25 — an engine row decides through one function, with its cell's identity

Issue: [#634](https://github.com/asimov-agent/llgenie/issues/634)
PR: [#637](https://github.com/asimov-agent/llgenie/pull/637)
OpenSpec change: `engine-row-cell-identity`

## What was red

`engine-build` run `40215905868` (head `65c986f`), 4 of its rows red — and all four are the cells
`DEVICE_ONLY` names, with their measured reasons, because their CLI cannot import without a device:

| job | job id | binary |
|---|---|---|
| `engine-build-mlx-cuda` | 121236921730 | `mlx_lm.server` |
| `engine-build-tensorrt-llm-cuda` | 121236921755 | `trtllm-serve` |
| `engine-build-vllm-cuda` | 121236921778 | `vllm` |
| `engine-build-vllm-rocm` | 121236921865 | `vllm` |

```
E       AssertionError: tensorrt-llm/cuda binary trtllm-serve failed the flag check:
E         --help: documented but did not answer (exit 1, 1248 byte(s) of output)
E             ImportError: libcuda.so.1: cannot open shared object file: No such file or directory
E         every probed flag failed and / is NOT on the device-only exemption list: a binary that cannot
E         answer one flag on this runner proves nothing (add it to DEVICE_ONLY with a reason, or DISABLE
E         the cell — issue #625)
```

`and / is NOT on …` is the tell: empty engine, empty variant.

## Root cause

`tests/test_engine_version.py` re-implemented the row — its own `docker run … BINARY_PROBE`, its own
`parse_probe`, its own `decide` — and called the decider without the cell:

```python
verdict = ei.decide(documented, verdicts, policy)                 # the test
decide(documented, verdicts, policy, engine=spec["id"], variant=spec["variant"])  # binary_file_works
```

`DEVICE_ONLY.get((engine, variant))` therefore never matched on the pytest path: #625's exemption was
unreachable from the only job that needs it. `tests/test_engine_binary_flags.py` drove `decide()` directly
WITH the identity, so the unit suite tested the decider and never the caller that omitted it.

## Fix

While this was in flight, #632 (PR #633, `c5a45ff`) fixed the SYMPTOM at that call site and made `decide()`
refuse a `policy: device` verdict without the cell identity. This change fixes the CAUSE — the row was a second
implementation of the pipeline, which is why it drifted and could not inherit the fix.

- `tests/test_engine_version.py`: the flag case calls `engine_image.binary_file_works(spec)` — the same
  function `make test-engine-image` runs — and asserts its exit status, printing the captured per-flag table
  as the failure evidence. No local probe, no local decider.
- `tests/test_engine_binary_flags.py`: the seam test — the engine-row test's flag case names
  `binary_file_works(spec)` and carries no `BINARY_PROBE`/`decide(`/`parse_probe(` of its own. The identity
  rule and both of its directions belong to #633 and are NOT duplicated here.
- README: names `binary_file_works` as the one deciding function and records why (issue #634).

## Verification

- `tests/test_engine_binary_flags.py`: `12 passed`, including the three new cases.
- The product path is untouched: `scripts/engine_image.py` is not modified, so the CLI row behaves exactly
  as before — the pytest row now joins it instead of duplicating it.
- Gates: `make openspec-validate NAME=engine-row-cell-identity`, `make lint`, `make check-workflows`,
  `make check-wiring`, `make check-docs`, `make test-unit`.
- The row's verdict now comes from the function `test_image` already runs for the same image, so the two
  cannot disagree; the next `engine-build` sweep proves the four cells end to end.
