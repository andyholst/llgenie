# agent-profiles-in-repo — proposal

Issue: [#791](https://github.com/asimov-agent/llgenie/issues/791)

## Why

The two live LLGenie host agents — `llgenie-planner` (orchestrator) and `llgenie-issse-implementer` —
keep their behaviour **outside** the repository, in `~/.hermes/profiles/<profile>/SOUL.md` plus that
profile's `skills/`. They hold the write credentials, and an instruction that changes their behaviour is
the most consequential change in this repository — and the only one with no review, no diff and no
history. Measured 2026-10-28: the planner's `SOUL.md` was rewritten and a new
`llgenie-bot-orchestration` skill written the same day, and `git log --all --oneline -- '*SOUL*'`
returned nothing. A profile reinstall, a Hermes upgrade or a new machine silently loses all of it.

The CI legs are the model to copy: their contracts live in `.hermes/skills/`, preloaded with
`hermes -s <name>` and gated by `make check-agent-skills` (issue #577). The repository can prove what
every bot leg was told and nothing about what the host agents were told.

## What Changes

- `agents/manifest.json` lists the profiles and their roles; `agents/<profile>/SOUL.md` and
  `agents/<profile>/skills/<name>/SKILL.md` carry their behaviour, mirroring the layout Hermes loads.
- `scripts/agent_profile_sync.py` + `make sync-agent-profile PROFILE=<p> [CHECK=1]` make the tree the
  source of truth: copy `agents/<p>/` into the live profile, or compare every carried file and name the
  first drift. It never deletes a live-only file (a profile holds memory-adjacent state and dozens of
  vendored skills) and never touches `config.yaml`, sessions or caches.
- `scripts/check_agent_profiles.py` + `make check-agent-profiles` (wired into `ci-unit`) refuses: a
  listed profile with no directory or no `SOUL.md`; a skill whose frontmatter `name:` differs from its
  directory; a secret-shaped value in a profile; and a `SOUL.md` that no longer states the never-merge
  rule.
- `agents/llgenie-planner/` and `agents/llgenie-issse-implementer/` are seeded from the live profiles,
  with the implementer's SOUL gaining the standing rules it was missing (never merge, one issue per
  branch, never prune unasked, behaviour lives in the repo).
- `.hermes/skills/README.md` states the three-tree split so a contributor cannot confuse a bot leg's
  skill with a host agent's behaviour.

## Decisions

- **The orchestrator's "never implement" is a report line, not a gate failure.** The owner mandated the
  never-merge rule; whether the orchestrator also states that it does not implement is the planner's own
  behaviour decision, and a gate that reds a PR over it would be the repository legislating an agent's
  SOUL. `make agent-profiles-report` shows the gap.
- **Sync is additive.** Mirroring deletions would turn "the repo carries one skill" into "the agent lost
  the other 59"; live-only paths are printed as notes.
- **Secrets are a hard failure.** A committed profile is text anyone can read; a token in it is a leaked
  token, and the patterns are deliberately broad because a false positive is one allowlist line.

## Out of scope

- The CI legs' contracts (`.hermes/skills/`, #577) — not moved, not re-gated.
- Profile memory, sessions and state databases — not behaviour, never committed.
