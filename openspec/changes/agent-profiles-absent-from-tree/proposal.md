# agent-profiles-absent-from-tree — proposal

Issue: [#1069](https://github.com/asimov-agent/llgenie/issues/1069)

## Why

`make check-agent-profiles` (`scripts/check_agent_profiles.py`) compares the host agents' behaviour
tree with the live profiles on the host that runs it — but **only in one direction**. Every comparison
iterates `tree_profile.rglob("*")` (`:356`, `:415`, `:462`) and asks whether the live file differs;
nothing enumerates a live file that has no tree counterpart. So a lane can carry whole unversioned
reference files and the gate stays green.

Measured at `main@ac12cae9` on this host (the gate reads `~/.hermes/profiles/`):

```
agents/llgenie-planner/skills/llgenie-bot-orchestration/                tree = 12 files
~/.hermes/profiles/llgenie-planner/skills/llgenie-bot-orchestration/    live = 33 files
live-only = 21   (issue #1069 measured 17 at #919 head e21e7b22; the drift continued overnight)
agents/llgenie-tester/skills/llgenie-pr-testing/                        live-only =  1
```

and the gate reports **zero** findings for any of those 22 paths — its 13 findings at `ac12cae9` are
all `live-longer` (12) and `live-edited-not-tree` (1). `_text_files(profile)` (`:220`) already
enumerates a profile's files; nothing subtracts the tree set from the live set.

This is the direction #1060 needs: "this behaviour exists on the host and was never versioned". A
gate that cannot see an unversioned file cannot gate the rule that behaviour is versioned.

## What Changes

- **A reverse-direction finding, `absent-from-tree`** (`absent_from_tree_findings()` in
  `scripts/check_agent_profiles.py`), wired into `findings()` and therefore into `check` and
  `report`: for every live file with no tree twin it emits one finding naming the profile, the
  relative path and the live size, and says the file exists only on the host.
- **The mirrored surface is bounded on purpose.** A live profile directory is a whole Hermes home —
  `state.db`, `sessions/`, `memories/`, `cron/`, `logs/`, `.curator_backups/`, `worker-outboxes/`
  and the *shared* skill library Hermes bundles into every profile (~4,800 files for the planner).
  None of that is lane behaviour, and reporting it would drown the 22 real findings. The reverse
  comparison therefore walks only what the tree is the source of truth for: `SOUL.md` and the files
  of each **tree skill directory** (`agents/<profile>/skills/<skill>/` mirrored at
  `~/.hermes/profiles/<profile>/skills/<skill>/`).
- **No regression:** the existing keys and their counts stay (a subset assertion in the tests, never
  an exact list — #1060 adds more findings as lanes are versioned).
- **A lane with no live profile on the host stays `absent-live`**: skipping the comparison is already
  the handled condition (`live_root()` returns `None`), and it must not produce a reverse finding.

## Benefit

An instruction a credential-holding agent runs under can no longer be live-only and invisible: the
file that was never versioned is named, with its lane and its size, by the gate that already fails on
drift. #1060 gets a red gate it can work down instead of a hand-built census.

## Not covered

- **Versioning the 22 live-only files themselves** — that is [#1060](https://github.com/asimov-agent/llgenie/issues/1060),
  one PR per lane; this change only makes them visible.
- **A whole live skill directory with no tree twin** (`software-development/llgenie-architecture-issue-pass`,
  `llgenie-pipeline-maintenance`, …): naming one requires deciding which live skills are lane behaviour
  rather than Hermes' shared library, which this change deliberately does not guess. Filed as its own
  issue — [#1086](https://github.com/asimov-agent/llgenie/issues/1086).
- **`make profile-drift` (Makefile:437) passes `--only live-longer`, which the script rejects** (it
  exits 2 with "unrecognized arguments"), so that host-only #928 control has never compared anything.
  Filed as its own issue — [#1087](https://github.com/asimov-agent/llgenie/issues/1087).

## Technical

- `scripts/check_agent_profiles.py`: new `absent_from_tree_findings(root, agents_dir, live=None)`,
  called from `findings()` beside `shrink_findings()` / `live_edited_findings()`; the module docstring's
  finding list gains the new key.
- `tests/test_agent_profiles.py`: one rejection per shape (a live-only reference file, a live-only
  `SKILL.md`, a clean mirror, the data/library noise a live profile carries, a lane with no live
  profile), plus the measured host census recorded as a subset of the existing keys.
- `Makefile`: the `check-agent-profiles` `## help` line names the reverse finding; no new target.
- `agent-wiki/2026-10-30-agent-profiles-absent-from-tree.md` + `docs/changes.d/<stem>.md`.
