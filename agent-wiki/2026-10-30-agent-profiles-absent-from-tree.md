# The agent-profile gate now sees the live side too

**Issue:** [#1069](https://github.com/asimov-agent/llgenie/issues/1069) · **OpenSpec change:**
`agent-profiles-absent-from-tree` · **PR:** (this branch) · **Follow-ups:** #1086, #1087

## What was verified against the spec

`scripts/check_agent_profiles.py` compared the tree and the live profile in one direction only: three
comparisons iterate `tree_profile.rglob("*")` (`:356`, `:415`, `:462`) and ask whether the live file
differs. A file the tree has never held was invisible, so a lane could carry whole unversioned
reference files and the gate stayed green.

Re-measured at `main@ac12cae9` (read 2026-10-30T20:56Z, `origin` = `asimov-agent/llgenie`, `AGENTS.md`
89,067 b / 1,330 l):

```
agents/llgenie-planner/skills/llgenie-bot-orchestration/             12 files
~/.hermes/profiles/llgenie-planner/skills/llgenie-bot-orchestration/ 33 files   -> 21 live-only
agents/llgenie-tester/skills/llgenie-pr-testing/                     ->  1 live-only
```

The issue measured 17 live-only planner files at the #919 head `e21e7b22`; the drift continued
overnight (`agent-profile-sync.md`, `verifying-pr-state.md` and three more landed live-only since).

**The new finding.** `absent_from_tree_findings()` walks the live mirror of `SOUL.md` and of each
skill directory **the tree carries**, subtracts the tree file set, and emits one `absent-from-tree`
finding per path: the lane, the path relative to the profile, and the live size plus the
`agents/<profile>/skills/<skill>/` remedy. It is wired into `findings()`, so `check` (exit 1) and
`report` both show it, and the `OK` line now also claims "no file exists only in the live profile"
when the comparison actually ran.

## Decisions taken

- **The surface is bounded, deliberately.** A live profile directory is a whole Hermes home: measured
  4,804 files for `llgenie-planner` (`state.db`, `sessions/`, `memories/`, `cron/`, `logs/`,
  `.curator_backups/blobs/*`, `worker-outboxes/*` and the ~200 bundled skills every profile carries).
  Walking the whole home would emit ~4,800 findings and bury the 22 real ones, so only the surface
  the tree is the source of truth for is compared. A live skill directory with **no** tree twin is a
  different question — it needs a rule for "lane behaviour vs shared library" — and is filed as #1086.
- **Bookkeeping is not behaviour.** Hidden names (`.DS_Store`, `.curator_state`) and `__pycache__` are
  skipped: the agent tooling writes those without anyone choosing to.
- **A fraction, not a verdict.** A finding names the path and the size, never the content: a live file
  can hold credentials and this gate prints to a console.
- **The existing findings are untouched.** `findings()` is the union of its three directions; the test
  drives a fixture where all three fire (one `live-longer`, one `live-edited-not-tree`, one
  `absent-from-tree`) and asserts the two older keys keep their counts. Subset assertions only, so
  #1060's versioning PRs add findings without reddening this gate's own test.

## Status

- `make check-agent-profiles` on the host: **exit 1**, 12 `live-longer`, 2 `live-edited-not-tree` and
  23 `absent-from-tree` findings — every one a real unversioned reference (#1060 works them down).
- Negative control, both directions, against a `HERMES_PROFILES_HOME` fixture built from the tree:
  add one live-only file → exit 1 naming it; remove it → exit 0. Plus the real host: a probe file
  under a live skill directory is named, and removing it returns the gate to its baseline findings.
- `tests/test_agent_profiles.py`: 115 pass in `llgenie/test:latest`, 11 of them new.
- CI has no live profiles, so the container suite exercises the tree-only half; the host half is
  recorded here, as #791's was.

## Follow-ups filed (out of scope for this change)

- **#1086** — a whole live skill directory with no tree twin (`software-development/llgenie-architecture-issue-pass`,
  `llgenie-pipeline-maintenance`, …) is still invisible; it needs a rule for lane behaviour vs the
  shared library.
- **#1087** — `make profile-drift` (Makefile:437) passes `--only live-longer`, which the script
  rejects with exit 2, so that host-only #928 control has never compared anything.
