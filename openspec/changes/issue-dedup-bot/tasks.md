# Tasks — issue-dedup-bot (issue #553)

- [x] 1. OpenSpec change: `proposal.md`, `specs/issue-dedup-bot/spec.md`, this checklist
- [x] 2. `scripts/issue_dedup.py`: protected set, candidates, best pair (Jaccard, older canonical), the `pick`/`apply` protocol, evidence-refusing close, canonical queued
- [x] 3. `Makefile`: `issue-dedup-pick`, `issue-dedup` (agent leg inside the image, redacted), `issue-dedup-apply`
- [x] 4. `.github/workflows/issue-dedupe.yml`: `cron: "51 */6 * * *"` (4x/day) + `workflow_dispatch`, byte-identical guard, pick → decide → apply, a crashed pick and an empty `dedup.md` both fail loudly
- [x] 5. `tests/test_issue_dedup.py`: 12 cases (each protected label, candidate filtering, pair choice, the file the agent reads, close+queue, no-evidence refusal, claimed copy untouched, distinct)
- [x] 6. `README.md` (section + the three commands + the dispatch table) and `agent-wiki/2026-10-23-issue-dedup-bot.md`
- [x] 7. Verified: `pytest tests/test_issue_dedup.py` 12 passed; `tests/test_workflow_guards.py` + `tests/test_dispatch_forms.py` + `tests/test_wiring.py` green; `make lint`, `make check-workflows`, `make check-docs`, `make openspec-validate NAME=issue-dedup-bot`, `make openspec-tasks-check`; `make test-unit` in the PR checks
- [x] 8. PR opened against `asimov-agent/llgenie:main` closing #553
