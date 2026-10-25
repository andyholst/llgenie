# Tasks

- [x] 1. `openspec/changes/rebase-bot-skill-comma` — proposal + `specs/rebase-bot-skill-comma/spec.md` (G/W/T, a `- **Test:**` line per scenario) + this checklist, written before the code (issue #641)
- [x] 2. `Makefile` — `REBASE_BOT_SKILLS := rebase-conflict,bot-unattended`; the leg references it so no literal comma reaches `$(call scrubbed_run,…)`; comment states the rule
- [x] 3. `tests/test_agent_legs_quoting.py` — derives every `scrubbed_run` leg from the Makefile, asserts balanced quotes under `make -n`, and asserts rebase-bot keeps both skills; proved to fail on the pre-fix Makefile (3 failed) and pass after (3 passed)
- [x] 4. `README.md` — the rebase-bot section names the `$(call)` comma trap and the variable
- [x] 5. `agent-wiki/2026-10-25-rebase-bot-skill-comma.md` — the work record, referencing issue #641 and its PR
- [x] 6. Verified: `make -n rebase-bot-agent` (2 quotes, `-s rebase-conflict,bot-unattended`), `make openspec-validate NAME=rebase-bot-skill-comma`, `make check-agent-skills`, `make check-wiring`, `make lint`, `make check-docs`, and the new test file in the test image
