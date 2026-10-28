# Tasks

- [x] 1. `scripts/engine_skill_gap.py`: `QUEUE_LABEL = "agent:implement"`, `_issue_labels()`, `ensure_queue_label()` — the label is applied explicitly after the create, read back, and a label that does not land raises naming the issue; `--dry` mutates nothing
- [x] 2. `open_issue()` repairs an existing open tracking issue that lost the queue label instead of skipping it, so a re-run fixes `#686`-style issues
- [x] 3. `issue_body()` names `make engine-skill-scaffold ENGINE="<registry name>"` as the first fix step and lists what stays to be filled
- [x] 4. `scripts/engine_skill_scaffold.py`: `slug()`, `backends()` (registry `CUDA / ROCm / CPU / Metal` -> the skill list, refusing a wording it cannot place), `skill_text()`, `scaffold()` with `--engine/--id/--registry/--out/--backends/--servable/--force/--dry/--json`; every unprovable key written EMPTY
- [x] 5. `make engine-skill-scaffold` exists, is in `.PHONY`, has a `make help` line and is documented in `README.md`
- [x] 6. Tests: `tests/test_engine_skill_scaffold.py` (6 cases, real `scaffold()` + real parser + real `validate()`) and the two label-routing cases in `tests/test_engine_skill_gap.py` (real `gh` executable on PATH, whose `issue create` drops the label as CI does)
- [x] 7. Both files green: `python -m pytest tests/test_engine_skill_scaffold.py tests/test_engine_skill_gap.py` in `llgenie/test:latest` — **82 passed**
- [x] 8. `agent-wiki/2026-10-27-engine-skill-automation.md` records the work (issue #757) and `CHANGES.md` indexes it
- [x] 9. `make lint`, `make check-docs`, `make check-wiring`, `make test-unit` and `make openspec-validate NAME=engine-skill-automation` exit 0
- [x] 10. `scripts/issue_implementer.py dispatch` scaffolds an engine tracking issue BEFORE the agent: it recognizes `engine_skill_gap.issue_title()`, writes the skill, and appends a `## Scaffold` section to `issue.md` (no file on a dry run, no section for a plain issue, a reported-not-fatal line when the store no longer names the engine)
- [x] 11. The dispatch path is green: `python -m pytest tests/test_issue_implementer.py tests/test_engine_skill_scaffold.py tests/test_engine_skill_gap.py` in `llgenie/test:latest` — **126 passed**
