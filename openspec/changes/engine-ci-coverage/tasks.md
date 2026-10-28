# engine-ci-coverage — tasks

- [x] `scripts/engine_coverage.py`: `variants_of`, `verdict`, `census`, `findings`, `check`/`report` CLI, `KNOWN_UNBUILT` with `exllamav3-rocm` (#103)
- [x] `Makefile`: `check-engine-coverage` + `engine-coverage-report` targets, both in `.PHONY`
- [x] `Makefile`: `ci-unit` runs `check-engine-coverage` immediately after `check-engine-params`
- [x] `tests/test_engine_coverage.py`: verdict rule, exception lifecycle, real tree green (7 cases)
- [x] `make check-engine-coverage` exits 0 on the committed tree and names `exllamav3-rocm` as the recorded gap
- [x] `scripts/issue_bot_gates.py`: `check-engine-coverage` classified in `DEFERRED` with its reason, so the new `ci-unit` gate is not a `test-unit` finding
- [x] docs: `README.md` target line, `docs/ENGINES.md` ordered pipeline, `docs/BOTS.md` sync ordering
- [x] `agent-wiki/2026-10-28-engine-ci-coverage.md` + the `CHANGES.md` index row
- [x] `make openspec-validate NAME=engine-ci-coverage` exits 0
- [x] `make lint`, `make check-wiring`, `make check-docs`, `make check-engine-coverage` green in the worktree
