# Tasks

- [x] 1. `README.md` rewritten as the user guide: what llgenie is, requirements, install, `llgenie` usage, downloader, top-tier, launch/serve, docs+gates, layout, license, environment — linking `docs/ARCHITECTURE.md`, `docs/ENGINES.md`, `docs/BOTS.md` and `CHANGES.md`
- [x] 2. `docs/BOTS.md` created from the moved automation prose (bot pipelines, legs-as-skills, implementer, secrets, transcript redaction, web reach, code review, merge policy, architecture bot, run-failure reactor, manual dispatch + the generated dispatch table, verification/CI, contributor rules, trigger guard, isolation)
- [x] 3. `docs/ENGINES.md` created from the moved engine prose (llama.cpp build rule, tree/backend selection, install targets, env seams, CI matrix, engine skills, on-demand builds, container images)
- [x] 4. `CHANGES.md` created as the change index: one row per `agent-wiki/` note (date, change, link, issue/PR), newest first, linked from the README
- [x] 5. `scripts/check_docs.py` gains the documentation surface (README + linked `docs/` pages), the `CHANGES.md` index checks (unindexed note, dangling row, README→index link), and the README-purity checks (issue-numbered heading, change-log heading, dispatch marker)
- [x] 6. `scripts/check_dispatch_forms.py` verifies the generated table in `docs/BOTS.md`, not the README
- [x] 7. `scripts/engine_bump.py` rewrites `tests/` and `docs/` only; `.github/workflows/engine-bump.yml` stages `docs/` instead of `README.md`
- [x] 8. `AGENTS.md` "Documentation is part of the change" amended: dated note + `CHANGES.md` row, README only for user-facing behaviour, a bot never writes the README; `Makefile` help text follows
- [x] 9. Tests updated for the new contract: `tests/test_check_docs.py` (rewritten: real tree, surface, index, README purity), `tests/test_dispatch_forms.py`, `tests/test_issue_bot_manual_pick.py`, `tests/test_auto_merge.py`, `tests/test_architecture_bot.py`, `tests/test_agent_nerve.py`, `tests/test_engine_bump.py`
- [x] 10. This change's own `agent-wiki/2026-10-26-readme-user-guide-changes-index.md` note + its `CHANGES.md` row
- [x] 11. Gates verified in `llgenie/test:latest`: `make test-unit` (the updated tests green), `make check-docs`, `make check-dispatch-forms`, `make lint`, `make check-workflows`, `make check-wiring`, `make openspec-validate NAME=readme-user-facing-changes-index` (all green: 5225 tests)
