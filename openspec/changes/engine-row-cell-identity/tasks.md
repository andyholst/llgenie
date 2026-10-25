# Tasks — engine-row-cell-identity

- [ ] 1. OpenSpec change (`proposal.md`, `specs/engine-row-verdict/spec.md`, this file)
- [ ] 2. `tests/test_engine_version.py`: the flag case calls `engine_image.binary_file_works(spec)` and
      asserts its exit status — no local probe, no local `decide(`
- [ ] 3. `tests/test_engine_binary_flags.py`: the row test carries no `BINARY_PROBE`/`decide(`; every
      `DEVICE_ONLY` cell is exempt with its own identity and red with an empty one
- [ ] 4. README: name the one function that decides an engine row
- [ ] 5. `agent-wiki/` entry naming #634 and the PR
- [ ] 6. Verified: `make test-unit` (the new tests), `make lint`, `make check-wiring`, `make check-docs`,
      `make check-workflows`, `make openspec-validate NAME=engine-row-cell-identity`, and the four red cells'
      verdict reproduced through `binary_file_works` against the real `binaries.json` manifest
