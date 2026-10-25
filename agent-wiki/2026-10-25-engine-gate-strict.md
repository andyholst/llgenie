# 2026-10-25 — a green engine row must mean the binary answered

Issue: [#625](https://github.com/asimov-agent/llgenie/issues/625)
PR: [#626](https://github.com/asimov-agent/llgenie/pull/626)
OpenSpec change: `engine-gate-strict`

## The audit that started it

Run 40204145334 swept 27 rows, 29/29 green. Reading each row's log:

| what the log showed | rows |
|---|---|
| a documented flag answered (exit 0) — genuine | 18 |
| **every** probe exit 1, green via `probe: device` | `vllm/cuda`, `vllm/rocm`, `tensorrt-llm/cuda`, `mlx/cuda` |
| `detect` "proved" a version that is a log timestamp or `0.0.0` | `llama.cpp-laurentzuijdwijk` cpu/rocm/vulkan, `sglang/rocm` |

`decide()` returned ok for any `device` cell whose flags all failed, and `test_image()` judged `detect` with
`re.search(r"\d+\.\d+")` — which `0.00.000.272 I srv  llama_server: initializing ...` satisfies.

## What changed

- `decide()`: at least one probed flag must exit 0. `probe: device` only carries a cell named in
  `DEVICE_ONLY`, and each entry states the measured reason (`#625 …`) — the four cells above are the entire
  list, so a new engine cannot inherit the escape.
- `version_proof()`: a semver or `pin <sha7+>` is a version; a timestamped log line and `0.0.0` are not.
  `test_image()` now fails naming what it saw.
- `sglang` detect reads `importlib.metadata` (its rocm wheel's `__version__` is `0.0.0`, the distribution is
  `0.5.21`); `llama.cpp-laurentzuijdwijk` stops documenting `--version` — its fork starts serving instead — and
  reports `pin 3c75be02f450`.
- `tests/test_engine_gate_strict.py` (7 tests) pins both halves and the two fixed detects.

## Verification

- Falsification against the old rule: `re.search(r"\d+\.\d+", "installed 0.00.000.272 I srv …")` → True (the
  bug), `version_proof(...)` → `""`; `decide(policy="device")` → ok False for `sglang/cuda` (unlisted) and True
  for `vllm/cuda` (listed, note quotes the reason).
- `7 passed` in `tests/test_engine_gate_strict.py`; `138 passed` across `test_engine_image_matrix.py`,
  `test_engine_supported_quants.py` and the rest of the engine suites.
- Gates: `make test-unit`, `lint`, `check-docs`, `check-wiring`, `check-workflows`, `check-engine-params`,
  `check-pr-authors`, `openspec-validate`.

## What the four `DEVICE_ONLY` cells still do not prove

On a GPU-less runner they prove the file exists plus a version-shaped `detect`, not that the CLI runs. mlx/cuda
was proved end to end on the maintainer's 4090 (`mlx_lm.server --help` exit 0, `Device(gpu, 0)`, OpenAI chat
OK); vllm and tensorrt-llm cuda/rocm would need the same treatment. A GPU runner would remove the exemption
entirely — that is the follow-up, not a widening of this list.
