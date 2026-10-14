# Tasks

- [x] 1. `data/unsupported-engines.json` records every registry engine llgenie does not ship, with `decision`, `decided`, `reason` and `issue`
- [x] 2. `scripts/engine_skill_gap.py` computes the gap (shipped / known-unsupported / unresolved), the models no engine can offer, and the per-engine list; `report`, `render`, `check` and `spawn` work
- [x] 3. `engine_skills.validate(..., unsupported=...)` tolerates dated decisions per engine and names an engine with no skill and no decision; `--allow-unskilled` is gone
- [x] 4. Makefile: `engine-skill-gap`, `render-engine-skill-gap`, `check-engine-skill-gap`, `spawn-engine-skill-issues`; `ci-unit` gates on the decisions file instead of `ALLOW_UNSKILLED=1`
- [x] 5. `data/engine-skill-gap.json` is rendered and committed
- [x] 6. `registry-sync.yml` renders/commits the per-engine gap, carries it in the PR body, and spawns one tracking issue per NEW unskilled engine with `issues: write`
- [x] 7. `tests/test_engine_skill_gap.py` covers the gap, the gate, the spawn, the per-engine list and the (arch, vram, ram) permutation drop; the existing registry-sync tests are updated to the decisions file, and the two existing permutation grids (`test_pick_matrix_arch_perms.py`, `test_pick_full_registry.py`) lock that no image-less engine is ever offered and that a model no engine can offer is skipped, named
- [x] 8. `tests/test_engine_skill_gap.py` is named in `make test-unit`, and `make lint` passes
- [x] 9. README documents the decisions file, the gap report, the gate and the spawned work item
- [x] 10. Issue #229 body reflects the wiring as implemented (options 1 and 2 landed: dated decisions + per-engine spawn)
- [x] 11. In `llgenie/test:latest`: `tests/test_engine_skill_gap.py`, `tests/test_registry_sync_trend.py`, `tests/test_engine_skills.py` and `tests/test_trend_list_matrix.py` pass (74 + 183), and on the host `make skills-validate REGISTRY=data/models.json UNSUPPORTED=data/unsupported-engines.json`, `make check-engine-skill-gap`, `make check-trend-list-matrix`, `make lint` and `make openspec-validate NAME=engine-skill-gap` exit 0
