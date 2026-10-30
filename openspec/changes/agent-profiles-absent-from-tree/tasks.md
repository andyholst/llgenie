# Tasks

- [x] `scripts/check_agent_profiles.py`: `absent_from_tree_findings(root, agents_dir, live=None)` —
      walk `SOUL.md` plus every **tree** skill directory's live mirror, subtract the tree set, emit
      `absent-from-tree` naming profile, relative path and live size.
- [x] Wire it into `findings()` beside `shrink_findings()` / `live_edited_findings()`; name the key in
      the module docstring's finding list.
- [x] A lane with no live profile produces no reverse finding (`live_root()` → None keeps the existing
      audible skip; `absent-live` stays a different condition).
- [x] Tests in `tests/test_agent_profiles.py`: live-only reference file, live-only file beside
      `SKILL.md`, clean mirror + one added file, profile data not reported, shared skill library not
      reported, lane with no live profile, `report` names the finding, and the three directions
      coexist (subset assertions, never the host's exact counts — 12 `live-longer`, 1
      `live-edited-not-tree` measured at `ac12cae9`).
- [x] `Makefile`: the `check-agent-profiles` `## help` line names the reverse finding (no new target,
      so no wiring change).
- [x] Negative control on the host, both directions: with `HERMES_PROFILES_HOME` on a fixture built
      from the tree, one added live-only file → exit 1 naming it, removed → exit 0; and a probe under
      this lane's real live skill directory is named, then removing it returns the gate to baseline.
- [x] `make check-agent-profiles` run against the real host reports the measured live-only files
      (24 at the final run; 21 planner + 1 tester at the first measurement) and exits 1.
- [x] `agent-wiki/2026-10-30-agent-profiles-absent-from-tree.md` + its `docs/changes.d/` row;
      `make check-docs` green.
- [x] `make openspec-validate NAME=agent-profiles-absent-from-tree` passes, plus the scoped
      `ci-unit` gates (`check-agent-profiles` in the CI shape, `check-wiring`, `check-docs`, the unit
      suite) green.
