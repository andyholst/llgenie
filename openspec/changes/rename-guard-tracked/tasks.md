# Tasks

- [x] 1. `openspec/changes/rename-guard-tracked` — proposal + spec (G/W/T with a `- **Test:**` line) + this checklist, written before the code (issue #350)
- [x] 2. `scripts/module_name_guard.py` — `_gitignore_patterns()`, `is_ignored()`, `live_files()`; `hits()` uses them
- [x] 3. `tests/test_rename_llgenie_serve.py` — `live_files()` delegates to the guard; a gitignored artifact naming the old module is not a finding
- [x] 4. Verified: 14 passed in the test image; RED on the pre-change tree (3 failed, one of them the new case)
- [x] 5. `agent-wiki/2026-10-26-rename-guard-tracked.md` records it
