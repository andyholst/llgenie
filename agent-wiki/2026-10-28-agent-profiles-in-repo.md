# agent-profiles-in-repo — 2026-10-28

## What changed

- **`agents/`** (new): `manifest.json` lists both host agents with a role; `agents/llgenie-planner/`
  carries `SOUL.md` (7,509 bytes, copied verbatim from the live profile) and
  `skills/llgenie-bot-orchestration/SKILL.md`; `agents/llgenie-issse-implementer/SOUL.md` carries the
  implementer's role text plus the standing rules it never stated in one place (never merge, one issue
  per branch, never prune unasked, behaviour lives in this repository).
- **`scripts/agent_profile_sync.py`** + `make sync-agent-profile PROFILE=<p> [CHECK=1]`: copies
  `agents/<p>/` into `~/.hermes/profiles/<p>/` (or `$HERMES_PROFILE_HOME`), and with `CHECK=1` compares
  every carried file, names the first drift and exits 1. Unknown profile → exit 2. It never deletes a
  live-only file and never touches `config.yaml`, sessions or caches.
- **`scripts/check_agent_profiles.py`** + `make check-agent-profiles` (wired into `ci-unit`) and
  `make agent-profiles-report`: four hard failures — a listed profile with no directory/`SOUL.md`, a
  skill whose frontmatter `name:` disagrees with its directory, a secret-shaped value, and a `SOUL.md`
  that dropped the never-merge rule.
- **`tests/test_agent_profiles.py`**: one case per rejection, plus sync→check agreement, the
  live-only-file rule, the unknown-profile exit code, the make-target wiring, and the repository's own
  profiles passing the gate.
- `.hermes/skills/README.md` states the three-tree split; `docs/BOTS.md` documents the targets.

## Why

The host agents hold the write credentials and their behaviour lived only in
`~/.hermes/profiles/<profile>/`: no diff, no history, no review, and a reinstall loses it. Measured
2026-10-28: `git log --all --oneline -- '*SOUL*'` returned nothing while both profiles' SOULs had been
rewritten that day. The CI legs already have this discipline (`.hermes/skills/` + `make check-agent-skills`,
#577); this gives the host agents the same, without moving the legs.

## Decisions

- **Sync is additive, never a mirror.** A profile holds memory-adjacent state and dozens of vendored
  skills; a mirroring sync would turn "the repo carries one skill" into "the agent lost the other 59".
  Live-only paths are printed as notes and left alone.
- **The orchestrator's "never implement" is a report line, not a gate failure.** The owner mandated the
  never-merge rule; whether the planner's SOUL also says it does not implement is the planner's own
  behaviour decision, and a gate over it would be the repository legislating an agent's SOUL. The report
  shows the gap so it stays visible.
- **Secrets are a hard failure with broad patterns.** A committed profile is readable text; a false
  positive costs one allowlist line, a false negative leaks a credential.
- **The seed is the live text, not a retyped summary.** `agents/llgenie-planner/SOUL.md` is the live file
  byte-for-byte (the issue's Technical excerpt stops at an inner code fence at 632 bytes of 7,509), so
  `CHECK=1` against the live profile can be 0 from day one.

## Gates

- `tests/test_agent_profiles.py` — passing (one case per rejection + the repo's own tree).
- `make check-agent-profiles` — OK on the seeded tree; `make agent-profiles-report` prints both profiles.
- `make lint`, `check-docs`, `check-wiring`, `openspec-validate NAME=agent-profiles-in-repo`,
  `openspec-tasks-check` — green.

## Related

Issue [#791](https://github.com/asimov-agent/llgenie/issues/791) · #577 (the CI legs' in-tree skills,
the precedent this copies) · #792 (bot preflight, the sibling "make the habit a gate" change).
