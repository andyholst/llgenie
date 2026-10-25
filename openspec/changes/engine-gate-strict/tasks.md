# Tasks

- [x] 1. `scripts/engine_image.py::decide()` requires at least one probed flag to exit 0; `probe: device` is no longer an exemption by itself
- [x] 2. `DEVICE_ONLY` names the four measured cells (vllm cuda/rocm, tensorrt-llm cuda, mlx cuda) with a reasoned, issue-tagged string each; an unlisted device cell fails naming both remedies
- [x] 3. `version_proof()` accepts a semver or `pin <sha7+>` and refuses a timestamped log line (`0.00.000.272 I srv …`) and `0.0.0`; `test_image()` uses it and names what it saw on failure
- [x] 4. `skills/engines/sglang/SKILL.md` detect reads the installed distribution's version (`importlib.metadata`), so rocm reports 0.5.21 not 0.0.0
- [x] 5. `skills/engines/llama.cpp-laurentzuijdwijk/SKILL.md`: `binary_flags: ["--help"]` (the fork has no `--version`) and `detect: echo "pin {pinned_short}"`; params + binaries regenerated
- [x] 6. `tests/test_engine_gate_strict.py` locks the rule both ways (7 tests) and the two fixed detects
- [x] 7. Falsified against the OLD rule: `re.search(r"\d+\.\d+", "installed 0.00.000.272 I srv …")` matched (True) while `version_proof()` returns `""`; `decide(policy=device)` is False for an unlisted cell and True for a listed one
- [x] 8. `README.md` states the flag rule, the `DEVICE_ONLY` list and the version-shape rule; `agent-wiki/2026-10-25-engine-gate-strict.md` records the audit
- [x] 9. Gates green: `make test-unit`, `make lint`, `make check-docs`, `make check-wiring`, `make check-workflows`, `make check-engine-params`, `make check-pr-authors`, `make openspec-validate NAME=engine-gate-strict`
