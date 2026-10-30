# agent-profiles-live-only-skill-dir — proposal

Issue: [#1086](https://github.com/asimov-agent/llgenie/issues/1086)

## Why

#1069 gave `scripts/check_agent_profiles.py` a reverse direction, but it walks only the skill
directories the TREE carries. A lane whose whole skill set is unversioned is therefore invisible: five
manifest profiles carry no `skills/` in the tree at all, so every skill they run under is live-only and
ungated — exactly the hole #1060 exists to close.

Measured at `main@d5fb875c` on this host (the gate reads `~/.hermes/profiles/`):

```
agents/llgenie-architect/                 SOUL.md only — no skills/ at all
~/.hermes/profiles/llgenie-architect/skills/software-development/llgenie-architecture-issue-pass   7 files
absent-from-tree findings at d5fb875c before this change                                        0 for it
```

and the five lanes with no tree `skills/` (`llgenie-architect`, `llgenie-documentation-maintainer`,
`llgenie-ci-pipelines-maintainer`, `llgenie-engine-improver`, and this lane) contribute nothing.

A second, independent defect fell out of the measurement: the reverse direction treated **any**
directory under a tree profile's `skills/` as a skill. `agents/llgenie-pr-reviever/skills/` carries a
Hermes CATEGORY (`software-development/`) holding the lane's one skill, so the walk compared the whole
live category and reported the shared library inside it — **52 false `absent-from-tree` findings**, all
of them Hermes' own skills, which buried the real ones. The mirror rule is the sync's own
(`agent_profile_sync.py` writes `dest / rel`), so both directions must key on the relative path of a
real skill directory, not on a name or a bare directory.

## What Changes

- **A live skill DIRECTORY with no tree counterpart becomes one `absent-from-tree` finding**
  (`absent_from_tree_findings()`), naming the lane, the directory's path and its file count — one
  finding per directory, never one per file.
- **"Lane behaviour" is decided structurally, never by a name list.** A live skill is the machine's
  library, not the lane's, when any of these hold:
  - Hermes's own install records name it — `skills/.bundled_manifest` (the bundle it ships) and
    `skills/.hub/lock.json` (the hub packages it fetched);
  - it also exists in the shared library the profiles are seeded from — `<hermes-home>/skills`, the
    sibling of the `profiles/` directory;
  - it is a symlink out of the profile (`diagnose-crash -> /usr/share/omarchy/…`).
  Bookkeeping (hidden names, `__pycache__`, `.archive/`, `.hub/`) and the profile's data are not under
  `skills/` and stay unreported, as #1069 already established.
- **A skill directory is a directory carrying a `SKILL.md`.** That is what fixes the 52 false findings:
  `skills/software-development/` is Hermes's category, not a skill, so the file-level mirror now uses
  the same relative path the sync writes instead of a catalogue of every directory.
- **Without the shared library the directory comparison is skipped audibly**, never guessed: the gate
  says it did not compare rather than naming the ~116 skills every profile carries.
- **No regression:** the existing keys and counts keep their meaning (subset assertions in the tests),
  `absent-live` lanes stay silent, and `check` / `report` both read the new findings through
  `findings()`.

## Benefit

Every lane's unversioned behaviour is named by the gate, not by a hand-built census: the five lanes
with no tree `skills/` now produce one finding per unversioned skill, the library stops drowning them,
and #1060's "every lane-specific live skill has a counterpart under `agents/<profile>/skills/`" becomes
a gate that fails closed.

## Not covered

- **Versioning these skills** — that is [#1060](https://github.com/asimov-agent/llgenie/issues/1060),
  one PR per lane; this change only makes them visible.
- **`make profile-drift` passes `--only live-longer`, which the script rejects** (exit 2), so that
  host-only control has never compared anything — its own issue,
  [#1087](https://github.com/asimov-agent/llgenie/issues/1087).

## Technical

- `scripts/check_agent_profiles.py`: `shared_library()`, `installed_library_names()`, `_skill_dirs()`;
  `absent_from_tree_findings()` walks live skill directories by relative path and emits one
  `absent-from-tree` finding per unmirrored directory; `main()` gains the audible no-library caveat; the
  module docstring's finding list gains the directory key.
- `tests/test_agent_profiles.py`: one rejection per shape (live-only directory, live-only directory
  beside a versioned skill, bundle/hub/shared library, symlink out of the profile, a tree category that
  is not a skill), the negative control through `main(["check", …])` (red naming the path, green once
  removed), and the audible skip with no shared library. Fixtures create the shared library beside
  `profiles/`, as the host has it.
- Measured at `main@d5fb875c`: 116 skills per lane profile, 59 in `.bundled_manifest`, 12 in
  `.hub/lock.json`, 116 in `~/.hermes/skills`; 79 `absent-from-tree` findings before this change (52 of
  them the category false positive), 35 at the first read after it and 37 at the final run (the live
  profiles move while a PR is open) — 30 files inside mirrored skills plus 7 live-only directories.
- `Makefile`: the `check-agent-profiles` `## help` line names the directory finding; no new target.
- `agent-wiki/2026-10-30-agent-profiles-live-only-skill-dir.md` + `docs/changes.d/<stem>.md`.
