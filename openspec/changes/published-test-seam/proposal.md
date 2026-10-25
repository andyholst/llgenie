# published-test-seam — proposal

Issue: [#621](https://github.com/asimov-agent/llgenie/issues/621)

## Why

`main` at `a24e22f` is red: six `test-published-*` jobs (`llama.cpp` cpu/cuda/rocm/vulkan, `strata` cuda/rocm)
fail in the last step of `make test-published-engine` —

```
LLGENIE_PUBLISHED_PULLED=1 LLGENIE_TEST_ENGINE="llama.cpp" LLGENIE_TEST_ARCH="cpu" \
  python3 -m pytest -q -p no:cacheprovider tests/test_published_engine_binary.py
/usr/bin/python3: No module named pytest
```

— while the pull, the digest check and the binary's own flags all passed
(`version: 0.7.0-dev (build 11870, commit 74bca3950)`).

The recipe called pytest as a **host** command. Every other test stage in this repo runs through a seam that
provides pytest: `$(TEST_RUN)` (test image in CI, the venv on a dev host) or `$(call engine_test,…)` (the test
image with the engine's env). The runner has `/usr/bin/python3` and no pytest, so that line can only fail.

It stayed invisible because the published matrix was empty (`test-published-${{ matrix.engine }}-${{ matrix.variant }} → skipping`, 0 jobs) until #616 re-populated the rows from the committed params. The one run that
would have caught it did not exist.

## What Changes

- **`Makefile::test-published-engine`**: the binary-flag pytest runs in the **test image** through
  `$(call engine_test,…)`, with `LLGENIE_PUBLISHED_PULLED`, `LLGENIE_TEST_ENGINE` and `LLGENIE_TEST_ARCH`
  passed in — exactly how `test-engine-image` runs `tests/test_engine_version.py`.
- **`tests/test_make_pytest_seam.py`** (new, discovered by the aggregator): every recipe line that runs
  `python3 -m pytest` must carry one of the seams (`$(TEST_RUN)`, `$(ENGINE_TEST_RUN)`,
  `$(call engine_test,`, `llgenie/test:latest`), and `test-published-engine` must pass its env through
  `engine_test`. The parser joins `\`-continuations and ignores recipe comments.
- **`README.md`**: the `test-published-engine` entry says the flag check runs in the test image.

## Not covered

- The engines' own build/verify behaviour: unchanged — this is the test-harness seam only.
- The `engine-build` matrix's roster (rows like `freetoken`, `litert`, `mlx`): their own issues.
- Any other recipe that shells out to a tool the runner may lack: this change guards pytest specifically,
  because that is the one measured.

Refs: #102 (the published-image test), #204 (the binary-flag gate), #616 (the sweep that re-populated the
matrix), #120 (one seam per stage).
