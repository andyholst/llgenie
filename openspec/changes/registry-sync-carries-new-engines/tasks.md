# Tasks

- [x] 1. Measured the block: the sync job dies at `make skills-validate REGISTRY=data/models.json UNSUPPORTED=data/unsupported-engines.json` on 16 engines upstream had just started listing (`registry 40 engines, 16 error(s)`), before `spawn-engine-skill-issues` and the PR step — so no sync PR since 2026-10-13 and no tracking issue for any new engine
- [x] 2. `scripts/engine_skills.py validate(..., allow_new_engines=False)` + `--allow-new-engines`: a new engine with no skill and no decision is named and tolerated; the strict form still errors; a skill whose engine left the registry still fails either way
- [x] 3. `Makefile`: `skills-validate` forwards `ALLOW_NEW_ENGINES=1` and the help/comment says it is the data-carrying scope, never ci-unit's
- [x] 4. `.github/workflows/registry-sync.yml`: the check step passes `ALLOW_NEW_ENGINES=1`, with the deadlock and the ci-unit split stated in the step's comment
- [x] 5. `AGENTS.md` + `docs/BOTS.md`: the rule and the operational record (which scope runs where, and why)
- [x] 6. Tests: `tests/test_registry_sync_trend.py` (carrying vs strict, the sync step's exact scope, ci-unit not passing the flag), `tests/test_engine_skill_gap.py` (the sync still spawns issues and never runs the ci-unit gate)
- [x] 7. Verified on the REAL new store in a throwaway worktree: `make skills-validate … ALLOW_NEW_ENGINES=1` → `0 error(s)`, the same command without it → `16 error(s)`; `check-registry` 0 losses (81 drift notes), `check-quant-catalog`, `render-trend-list-matrix` (81 cases), `render-engine-skill-gap`, `engine-skill-gap` report all exit 0
- [ ] 8. `agent-wiki/2026-10-26-registry-sync-carries-new-engines.md` + its `CHANGES.md` row
- [ ] 9. Gates: `make test-unit`, `make check-docs`, `make check-workflows`, `make check-wiring`, `make lint`, `make openspec-validate NAME=registry-sync-carries-new-engines`
- [ ] 10. Re-dispatch `registry-sync` on `main` after the merge and confirm it reaches the PR step (the end-to-end proof)
