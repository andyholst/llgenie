# Tasks — fix-bot-no-pr

- [x] 1. OpenSpec change (`proposal.md`, `specs/fix-bot-sweep/spec.md`, this file)
- [x] 2. `scripts/resolve_run_pr.py`: `resolve --allow-none` answers "no PR" with exit 0 and an empty
      `number=` line; the default (merge gate) stays a loud exit 1
- [x] 3. `Makefile`: `fix-bot-resolve` target (the fix-bot's one code path) + `.PHONY` entry
- [x] 4. `.github/workflows/fix-bot.yml`: the sweep's resolution step calls `make fix-bot-resolve` and
      says what an empty answer means
- [x] 5. `tests/test_resolve_run_pr.py`: the lenient answer, the strict answer, the make target and both
      workflows' call sites
- [x] 6. README (the fix-bot section + the target list) and an `agent-wiki/` entry naming #629 and the PR
- [x] 7. Verified: `make test-unit` (the new tests), `make lint`, `make check-wiring`, `make check-docs`,
      `make openspec-validate NAME=fix-bot-no-pr`, and the fix-bot resolution driven end to end against a
      fake `gh` that answers nothing
