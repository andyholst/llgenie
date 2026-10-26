# Tasks

- [x] 1. `openspec/changes/openspec-validate-all` — proposal + spec (G/W/T, a `- **Test:**` line per scenario) + this checklist, written before the code (issue #156)
- [x] 2. `Makefile` — `openspec-validate-all` (`openspec validate --changes`), `.PHONY`, `##` help line; `ci-openspec` runs it
- [x] 3. `scripts/loop_harness.py` — the openspec stage validates all changes unless `NAME` is set
- [x] 4. `tests/test_openspec_gate.py` — ci-openspec runs the all-changes target; the loop's default does too
- [x] 5. Found and fixed by the new gate: `engine-push-requires-binary` had a requirement with no scenario
- [x] 6. Verified: `make openspec-validate-all` → 208 changes, 0 failed; RED before the fix (2 failed: that change and this one, while it was still empty)
- [x] 7. `README.md` + `agent-wiki/2026-10-26-openspec-validate-all.md` record it
