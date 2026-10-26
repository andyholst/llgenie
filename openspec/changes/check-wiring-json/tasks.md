# Tasks

- [x] 1. `openspec/changes/check-wiring-json` — proposal + spec (G/W/T, a `- **Test:**` line) + this checklist, written before the code (issue #395)
- [x] 2. `scripts/check_wiring.py` — `graph()` returns `named_by_target`; the `json` branch serialises `workflow_targets` as sorted lists
- [x] 3. `tests/test_wiring.py` — the subcommand exits 0 with exactly the three keys and no sets; RED on the pre-change tree (1 failed), GREEN after (11 passed)
- [x] 4. Verified: `python3 scripts/check_wiring.py json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sorted(d))'` → `['named_by_target', 'reachable', 'workflow_targets']`, 219 targets / 19 workflows
- [x] 5. `agent-wiki/2026-10-26-check-wiring-json.md` records it
