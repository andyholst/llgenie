# Tasks

- [x] 1. `Makefile::test-published-engine`: the binary-flag pytest runs through `$(call engine_test,…)` in the test image, with `LLGENIE_PUBLISHED_PULLED` / `LLGENIE_TEST_ENGINE` / `LLGENIE_TEST_ARCH` passed in
- [x] 2. `tests/test_make_pytest_seam.py`: every recipe line running `python3 -m pytest` must carry `$(TEST_RUN)`, `$(ENGINE_TEST_RUN)`, `$(call engine_test,` or `llgenie/test:latest`; the published target must use `engine_test` with its env
- [x] 3. Falsified: with the Makefile line stashed (the old host call) the new test fails naming it; restored, it passes
- [x] 4. `README.md`'s `test-published-engine` entry says the flag check runs in the test image (issue #621)
- [x] 5. `agent-wiki/2026-10-25-published-test-seam.md` records the work with the issue and the PR
- [x] 6. Gates green: `make test-unit`, `make lint`, `make check-docs`, `make check-wiring`, `make check-workflows`, `make check-dispatch-forms`, `make check-pr-authors`, `make openspec-validate NAME=published-test-seam`
- [x] 7. The `engine-build` dispatch (`workflow_dispatch` run 40199122842) monitored: rows build and verify through `make build-engine` + `make test-engine-stage`, with the same test-image seams this change repairs
