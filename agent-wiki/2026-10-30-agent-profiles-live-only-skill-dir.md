# The agent-profile gate now sees a whole live-only skill directory

**Issue:** [#1086](https://github.com/asimov-agent/llgenie/issues/1086) · **OpenSpec change:**
`agent-profiles-live-only-skill-dir` · **PR:** (this branch) · **Comes from:** #1069 (PR #1114)

## What was verified against the spec

`scripts/check_agent_profiles.py` gained a reverse direction in #1069, but it walked only the skill
directories the TREE carries. Five manifest lanes carry no `skills/` in the tree at all
(`llgenie-architect`, `llgenie-documentation-maintainer`, `llgenie-ci-pipelines-maintainer`,
`llgenie-engine-improver`, `llgenie-issse-implementer`), so every skill they run under was invisible.

Re-measured at `main@d5fb875c` (read 2026-10-30T22:40Z, `origin` = `asimov-agent/llgenie`):

```
absent-from-tree findings before this change: 79
  of which 52 were the SAME live shared library, reported under
  llgenie-pr-reviever/skills/software-development/  (a CATEGORY mistaken for a skill)
after this change: 35 at the first read, 37 at the final run
  30 files inside tree-carried skills  +  7 whole live-only skill directories
```

The live profiles move while a PR is open (a lane edits its skill mid-run), so the count is a
snapshot of one read, not a fixed number: `35` at 22:40Z, `37` at 23:52Z, the two extra a mirrored
skill's live-only files. The 7 directories:
`llgenie-architect/skills/software-development/llgenie-architecture-issue-pass` (7 files),
`llgenie-documentation-maintainer/skills/llgenie-docs-maintainer` (4),
`llgenie-ci-pipelines-maintainer/skills/llgenie-pipeline-maintenance` (10),
`llgenie-engine-improver/skills/software-development/llgenie-engine-improver` (5),
`llgenie-security/skills/software-development/agent-soul-versioning` (1),
`llgenie-issse-implementer/skills/software-development/bulk-mechanical-migration` (1), and
`llgenie-pr-merge-conflict/skills/development/llgenie-pr-rebase` (12) — a second, newer copy of a skill
the tree carries flat, with reference files and scripts the tree does not have.

## Decisions taken

- **"Lane behaviour" is structural, never a name list.** A live skill is the machine's library when
  Hermes's own install records name it (`skills/.bundled_manifest`, `skills/.hub/lock.json`), when the
  same skill exists in the shared library the profiles are seeded from (`<hermes-home>/skills` — the
  sibling of `profiles/`, measured at 116 skills and a superset of both install records), or when the
  directory is a symlink out of the profile. Everything else is the lane's. Measured per profile: 116
  live skills, 59 in the bundle, 12 in the hub lock, 116 in the shared library, 1–2 left over — and
  the leftovers are exactly the lane skills the issue names.
- **One finding per directory, not one per file.** A 12-file unversioned skill is one work item; 12
  findings would bury every other lane's. The detail carries the file count and the total size.
- **A skill directory carries a `SKILL.md`.** This is the fix for the 52 false findings: the tree's
  `skills/software-development/` is Hermes's category, and the mirror rule is the sync's own relative
  path (`agent_profile_sync.py` writes `dest / rel`), so both directions key on that. The same change
  removes a latent #1069 gap: a tree skill nested in a category was never compared file-by-file at all.
- **No library means no guess.** Without `<hermes-home>/skills` the gate cannot tell a lane's skill
  from the machine's; it prints `live-only skill DIRECTORIES were NOT compared` instead of naming the
  whole library. An audible skip is the house rule (`check` already prints one for a host with no
  profiles).
- **The existing keys are untouched.** `findings()` is the union of its directions and the tests assert
  subsets, never the host's exact counts — #1060 adds findings as lanes are versioned.

## Status

- `make check-agent-profiles` on the host: **exit 1**, 35 `absent-from-tree` (28 files + 7 directories),
  plus the older `live-longer` / `live-edited-not-tree` findings — all real, all unversioned behaviour
  (#1060 works them down).
- Negative control, both directions, through the real `check` entry point: a planted live-only skill
  directory → exit 1 naming `someone/skills/software-development/llgenie-lane-skill`; removed → exit 0.
  Fixtures create the shared library beside `profiles/`, as the host has it.
- `tests/test_agent_profiles.py`: 123 pass in `llgenie/test:latest` (8 new).
- CI has no live profiles, so the container suite exercises the tree-only half; the host half is
  recorded here, as #791's and #1069's were.

## Follow-ups (out of scope for this change)

- The five lanes' live-only skills are now named; **versioning them is #1060**, one PR per lane.
