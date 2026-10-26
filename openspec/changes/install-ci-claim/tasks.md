# Tasks

- [x] 1. `openspec/changes/install-ci-claim` — proposal + spec (G/W/T, a `- **Test:**` line per scenario) + this checklist, written before the code (issue #239)
- [x] 2. `Makefile` — `test-install-ci`'s `##` line is honest: a LOCAL one-container acceptance, with the `make ci-install` stages that cover the flow in CI
- [x] 3. `tests/fixtures/host-only-wiring.json` — the now-stale `test-install-ci` decision deleted
- [x] 4. `scripts/check_wiring.py` — a decision whose help line no longer claims CI coverage is stale
- [x] 5. `tests/test_wiring.py` — a case for the stale decision; the real tree still passes `make check-wiring`
- [x] 6. Verified: `make check-wiring` OK (201 documents, 197 in CI); the rule fires on the pre-fix state ("no longer claims CI coverage … delete it")
- [x] 7. `agent-wiki/2026-10-26-install-ci-claim.md` records it
