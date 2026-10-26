# Tasks

- [x] 1. `openspec/changes/sglang-version-not-pin` — proposal + spec (G/W/T with a `- **Test:**` line) + this checklist, written before the code (issues #636/#650)
- [x] 2. `skills/engines/sglang/SKILL.md` — the `0.0.0` fallback is `{version}` (the pinned version), not `pin {pinned_short}`; params regenerated
- [x] 3. `tests/test_engine_skills_pipefail.py` — no skill may print the sha as its version
- [x] 4. Verified in the published rocm image: the fixed detect prints `sglang 0.5.22`; `tests/test_engine_skills.py` + `test_engine_skills_pipefail.py` → 97 passed; `make check-engine-params` → 0 stale
- [x] 5. `README.md` + `agent-wiki/2026-10-26-sglang-version-not-pin.md` record the change and reference issues #636/#650
