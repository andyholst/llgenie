# Tasks

- [x] 1. File the issue with measured evidence (issue #309): the `--json comments` crash in `make rebase-bot-sweep` and in run 38810528684, the swallowed `set +e` no-op, and `--commenter github-actions[bot]` returning `[]`.
- [x] 2. Fix `rebased_today()` to use `gh`-valid argv (`search prs --json number` then `pr view --json comments`).
- [x] 3. Make `rebase-bot.yml`'s sweep step fail loudly when the sweep exits non-zero.
- [x] 4. Add the tests (valid-argv assertion; today's marker found; another day's ignored; the step fails loudly).
- [x] 5. Prove the tests fail on the pre-fix tree and pass after (rule 6c): `4 failed, 15 deselected` pre-fix, 19 passed after.
- [x] 6. Add an `agent-wiki/` entry citing #309/#310.
- [x] 7. Verified: `make lint`, `make openspec-validate NAME=rebase-sweep-valid`, `make check-wiring`, `make check-docs`, and `tests/test_rebase_bot_sweep.py` 19 passed in the test image.
