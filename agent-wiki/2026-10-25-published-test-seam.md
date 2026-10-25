# 2026-10-25 — the published-image test runs pytest in the test image

Issue: [#621](https://github.com/asimov-agent/llgenie/issues/621)
PR: [#622](https://github.com/asimov-agent/llgenie/pull/622)
OpenSpec change: `published-test-seam`

## What was red

`main` at `a24e22f` (CI run 40196270744) failed six jobs — `test-published-llama.cpp-{cpu,cuda,rocm,vulkan}`
and `test-published-strata-{cuda,rocm}` — all in the last step of `make test-published-engine`:

```
LLGENIE_PUBLISHED_PULLED=1 LLGENIE_TEST_ENGINE="llama.cpp" LLGENIE_TEST_ARCH="cpu" \
  python3 -m pytest -q -p no:cacheprovider tests/test_published_engine_binary.py
/usr/bin/python3: No module named pytest
make: *** [Makefile:899: test-published-engine] Error 1
```

Everything before it had passed: the image pulled, the digest matched `:cpu`, and the binary answered
`--version --help -h` (`version: 0.7.0-dev (build 11870, commit 74bca3950)`).

## Root cause

The recipe ran pytest as a **host** command. Every other test stage in the repo runs through a seam that
provides pytest — `$(TEST_RUN)` (test image in CI, venv on a dev host) or `$(call engine_test,…)` (test image
with the engine's env). The GitHub runner has `/usr/bin/python3` and no pytest.

It stayed invisible because the published matrix had no rows (`test-published-${{ matrix.engine }}-${{ matrix.variant }} → skipping`, 0 jobs) until #616 re-populated it from the committed params — the target was
never exercised by the job that would have failed.

## Fix

`test-published-engine` now runs the binary-flag pytest through `$(call engine_test,…)` with
`LLGENIE_PUBLISHED_PULLED`, `LLGENIE_TEST_ENGINE` and `LLGENIE_TEST_ARCH` passed into the container, exactly
like `test-engine-image` runs `tests/test_engine_version.py`.

`tests/test_make_pytest_seam.py` (new, auto-discovered by `scripts/unit_tests.py`) joins `\`-continuations,
skips recipe comments, and fails if any recipe line runs `python3 -m pytest` without one of the seams; it also
pins that `test-published-engine` carries its env through `engine_test`.

## Verification

- Falsified: with the Makefile line reverted to the old host call, the new test fails naming that exact line;
  with the fix it passes (`1 passed`).
- `make -n test-published-engine ENGINE=llama.cpp ARCH=cpu` renders a `docker run … llgenie/test:latest` with
  `LLGENIE_PUBLISHED_PULLED=1` in its env.
- `make lint`, `make check-workflows`, `make check-docs`, `make check-wiring`, `make check-dispatch-forms`,
  `make check-pr-authors`, `make openspec-validate NAME=published-test-seam` green; full `make test-unit` on
  the branch.
- The `engine-build` dispatch the maintainer started (run 40199122842, `a24e22f`) was monitored while this
  landed: its rows run `make build-engine` + `make test-engine-stage`, the same test-image seams, and none had
  failed at the time of writing.

## Why the dispatcher itself is fine

`gh workflow list` shows `engine-build — …` active (id 395994204); `gh workflow run engine-build.yml` produced
run 40199122842; the run's `guard` and `matrix` jobs passed and 29 build rows were created. The failures were
in the shared Makefile target, not in the dispatch surface — and `make check-dispatch-forms` (which keeps the
README's dispatch table generated from the workflow files) passes with `engine-build.yml` listed.
