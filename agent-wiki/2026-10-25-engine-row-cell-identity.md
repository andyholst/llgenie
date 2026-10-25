# 2026-10-25 — an engine row decides through one function, with its cell's identity

Issue: [#634](https://github.com/asimov-agent/llgenie/issues/634)
PR: _this branch_
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

- `tests/test_engine_version.py`: the flag case calls `engine_image.binary_file_works(spec)` — the same
  function `make test-engine-image` runs — and asserts its exit status, printing the captured per-flag table
  as the failure evidence. No local probe, no local decider.
- `tests/test_engine_binary_flags.py`: three regression tests — every `DEVICE_ONLY` cell is exempt with its
  own identity, the SAME verdicts with no identity are red (the bug's exact shape), and the engine-row test's
  text carries no `BINARY_PROBE`/`decide(`/`parse_probe(` of its own.
- README: names `binary_file_works` as the one deciding function and records why (issue #634).

## Verification

- `tests/test_engine_binary_flags.py`: `12 passed`, including the three new cases.
- The product path is untouched: `scripts/engine_image.py` is not modified, so the CLI row behaves exactly
  as before — the pytest row now joins it instead of duplicating it.
- Gates: `make openspec-validate NAME=engine-row-cell-identity`, `make lint`, `make check-workflows`,
  `make check-wiring`, `make check-docs`, `make test-unit`.
- The four cells' verdicts are reproduced hermetically through the shipped `decide()` with the real
  `DEVICE_ONLY` entries; the images themselves are re-proved by the next `engine-build` sweep, whose rows
  now call the same function this test calls.
