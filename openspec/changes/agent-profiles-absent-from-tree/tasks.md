# Tasks

- [ ] `scripts/check_agent_profiles.py`: `absent_from_tree_findings(root, agents_dir, live=None)` —
      walk `SOUL.md` plus every **tree** skill directory's live mirror, subtract the tree set, emit
      `absent-from-tree` naming profile, relative path and live size.
- [ ] Wire it into `findings()` beside `shrink_findings()` / `live_edited_findings()`; name the key in
      the module docstring's finding list.
- [ ] A lane with no live profile produces no reverse finding (`live_root()` → None keeps the existing
      audible skip; `absent-live` stays a different condition).
- [ ] Tests in `tests/test_agent_profiles.py`: live-only reference file, live-only file beside
      `SKILL.md`, clean mirror + one added file, profile data not reported, shared skill library not
      reported, lane with no live profile, `report` names the finding, and the host census keeps the
      pre-existing keys as a SUBSET (12 `live-longer`, 1 `live-edited-not-tree` measured at
      `ac12cae9`).
- [ ] `Makefile`: the `check-agent-profiles` `## help` line names the reverse finding (no new target,
      so no wiring change).
- [ ] Negative control on the host, both directions, with `HERMES_PROFILES_HOME` pointing at a fixture
      built from the tree: add one live-only file → exit 1 naming it; remove it → exit 0.
- [ ] `make check-agent-profiles` run against the real host reports the measured 22 live-only files
      (21 planner + 1 tester) and exits 1.
- [ ] `agent-wiki/2026-10-30-agent-profiles-absent-from-tree.md` + its `docs/changes.d/` row;
      `make check-docs` green.
- [ ] `make openspec-validate NAME=agent-profiles-absent-from-tree` passes, plus the scoped
      `ci-unit` gates (`check-agent-profiles`, `check-wiring`, `check-docs`, unit suite) green.
