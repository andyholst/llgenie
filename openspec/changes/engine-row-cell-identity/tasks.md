# Tasks — engine-row-cell-identity

- [x] 1. OpenSpec change (`proposal.md`, `specs/engine-row-verdict/spec.md`, this file)
- [x] 2. `tests/test_engine_version.py`: the flag case calls `engine_image.binary_file_works(spec)` and
      asserts its exit status — no local probe, no local `decide(`
- [x] 3. `tests/test_engine_binary_flags.py`: the row test carries no `BINARY_PROBE`/`decide(`/`parse_probe(`
      of its own (the identity rule itself is #633's and is not duplicated here)
- [x] 4. README: name the one function that decides an engine row
- [x] 5. `agent-wiki/` entry naming #634 and the PR
- [x] 6. Verified: `make test-unit`, `make lint`, `make check-wiring`, `make check-docs`,
      `make check-workflows`, `make openspec-validate NAME=engine-row-cell-identity`
