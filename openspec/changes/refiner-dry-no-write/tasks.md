# Tasks

- [x] 1. `openspec/changes/refiner-dry-no-write` — proposal + spec (G/W/T with a `- **Test:**` line) + this checklist, written before the code (issue #352)
- [x] 2. `scripts/issue_refiner.py::pick()` — dry writes nothing, says what it would write, returns `{"dry": True}`
- [x] 3. `tests/test_issue_refiner.py` — dry leaves no file, real run writes it; RED on the pre-change tree (1 failed), GREEN after (22 passed)
- [x] 4. `agent-wiki/2026-10-26-refiner-dry-no-write.md` records it
