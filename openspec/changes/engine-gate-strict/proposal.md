# engine-gate-strict — proposal

Issue: [#625](https://github.com/asimov-agent/llgenie/issues/625)

## Why

Run 40204145334 swept all 27 rows and reported 29/29 green. Auditing every row's own log shows a green row does
not always mean "the binary works":

- **4 rows answered NOTHING and still passed.** `vllm/cuda`, `vllm/rocm`, `tensorrt-llm/cuda`, `mlx/cuda`:
  every probed flag exited 1 (`in _compute_kwargs`, `line 1, in <module>`, `Traceback …`), and
  `decide()`'s `if policy == "device": return {"ok": True, …}` accepted them on the promise that the
  entrypoint `detect` would prove a version.
- **4 rows "proved" a version that is not a version.** `llama.cpp-laurentzuijdwijk` cpu/rocm/vulkan reported
  `installed 0.00.000.272 I srv  llama_server: initializing ...` — a timestamped server log line — because that
  fork does not implement `--version` (it starts serving), yet its manifest documented `--version`; and
  `sglang/rocm` reported `installed 0.0.0` while `sglang/cuda` reported `0.5.21` (its `detect` trusted
  `sglang.__version__`, which the rocm wheel leaves at `0.0.0`).
- `test_image()`'s only judge was `re.search(r"\d+\.\d+", detect_output)`, so `0.00.000.272` and `0.0.0` both
  passed.

`push()` re-runs `test_image()`, so these escapes also publish to GHCR.

## What Changes

- **`scripts/engine_image.py::decide()`**: at least one probed flag must exit 0, always. The `probe: device`
  policy no longer returns ok by itself; it may only carry a cell that is in the new **`DEVICE_ONLY`** list,
  and every entry states the measured reason and the issue. An unlisted `device` cell fails with a message that
  names both remedies (list it deliberately, or `DISABLE` it).
- **`version_proof()`**: the entrypoint `detect` output must prove a **version shape** — a semver
  (`0.5.21`, `0.32.0+cpu`, `0.7.0-dev`) or `pin <sha7…>` for an engine whose upstream prints none. A
  timestamped log line (`\d+\.\d+\.\d+ I srv …`) and the placeholder `0.0.0` are refused, and `test_image()`
  now fails naming what it saw instead of `re.search(r"\d+\.\d+")`.
- **`skills/engines/sglang/SKILL.md`**: `detect` reads the installed distribution's version
  (`importlib.metadata`), so rocm reports `0.5.21` instead of `0.0.0`.
- **`skills/engines/llama.cpp-laurentzuijdwijk/SKILL.md`**: `binary_flags: ["--help"]` (the fork has no
  `--version`), and `detect: echo "pin {pinned_short}"` — the image's build identity, which the gate accepts
  as a version proof.
- Regenerated `containers/engines/params/{sglang,llama.cpp-laurentzuijdwijk}.json` and
  `containers/engines/binaries.json` (`make generate-engine-params`), README, and a dated agent-wiki record.
- **`tests/test_engine_gate_strict.py`**: hermetic tests for both halves — a log stamp and `0.0.0` are not
  versions; an unlisted `device` cell is red; a listed one passes and quotes its reason; `probe: flags` never
  inherits the exemption; the exemption list is pinned to the four measured cells; and the two fixed `detect`
  commands are asserted.

## Not covered

- A GPU-enabled CI runner: with one, the four `DEVICE_ONLY` cells drop their exemption entirely. `mlx/cuda` was
  proved end to end on a 4090 host (`--help` exit 0, `Device(gpu, 0)`, OpenAI chat OK) — evidence, not coverage.
- `ollama --version`'s first line is a daemon warning (`Warning: could not connect …`); the version comes from
  `detect`, which is now version-shaped. Making the flag's own output carry the version is ollama's.
- The `DISABLED` cells (#103) and the build-vs-pull hash cache (#624).

Refs: #580 (per-flag verdicts), #614 (the sweep), #102/#204 (published gate), #103.
