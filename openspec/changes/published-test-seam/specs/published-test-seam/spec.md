# published-test-seam

## ADDED Requirements

### Requirement: a make recipe that runs pytest does so in the test image or the dev venv

A make recipe MUST NOT run `python3 -m pytest` on a bare host interpreter: the CI runner has a `python3`
and no pytest, so such a line fails with `No module named pytest` no matter what it tests. Every recipe that
needs pytest MUST run it through one of the repository's seams — `$(TEST_RUN)` (the test image in CI, the
venv on a dev host), `$(ENGINE_TEST_RUN)`, `$(call engine_test,…)` (the test image with the engine's env), or
an explicit `llgenie/test:latest` container.

WHEN a make recipe's command line runs pytest
THEN that command also carries one of those seams.

#### Scenario: every pytest invocation in the Makefile is seam-carried

- **Given** the Makefile's recipes, with `\`-continuations joined and recipe comments ignored
- **When** every line that runs `python3 -m pytest` is collected
- **Then** each one carries `$(TEST_RUN)`, `$(ENGINE_TEST_RUN)`, `$(call engine_test,` or `llgenie/test:latest`
- **Test:** `tests/test_make_pytest_seam.py::test_every_pytest_in_a_make_recipe_runs_through_the_test_seam`

#### Scenario: the published-image flag check carries its env into the test image

- **Given** `make test-published-engine ENGINE=<id> ARCH=<arch>` (issue #102)
- **When** its recipe is read
- **Then** the binary-flag pytest runs through `$(call engine_test,…)` with `LLGENIE_PUBLISHED_PULLED=1`,
  `LLGENIE_TEST_ENGINE` and `LLGENIE_TEST_ARCH` passed into the container
- **Test:** `tests/test_make_pytest_seam.py::test_every_pytest_in_a_make_recipe_runs_through_the_test_seam`

### Requirement: the published matrix's rows are exercised

The `linux-published` matrix MUST carry a row per published engine × arch, and each row MUST run the same
`make test-published-engine` a maintainer runs locally, so a target no row reaches cannot rot. The seam fix
above is what makes the first populated matrix green; the `engine-build` dispatch (#616) is the independent
whole-set sweep.

WHEN `main` carries the committed params with published images
THEN `test-published-<engine>-<arch>` jobs exist and run `make test-published-engine`, and they pass.

#### Scenario: a populated published matrix runs the target

- **Given** the params that produce `test-published-llama.cpp-cpu`
- **When** the job runs `make test-published-engine ENGINE=llama.cpp ARCH=cpu`
- **Then** the pull, the digest check, the binary-flag check (in the test image) and the serve check run, and
  the job's exit status is the target's
- **Test:** the `linux-published` CI matrix (`.github/workflows/published.yml`) →
  `make test-published-engine ENGINE=… ARCH=…`; the seam itself is locked by
  `tests/test_make_pytest_seam.py::test_every_pytest_in_a_make_recipe_runs_through_the_test_seam`
