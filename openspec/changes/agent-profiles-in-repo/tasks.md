# agent-profiles-in-repo — Tasks

Issue: [#791](https://github.com/asimov-agent/llgenie/issues/791)

- [x] 1. `agents/manifest.json` lists both profiles with a role; `agents/<profile>/SOUL.md` and `agents/<profile>/skills/<name>/SKILL.md` carry the behaviour.
- [x] 2. `scripts/agent_profile_sync.py` copies `agents/<p>/` into the live profile, and `check` names the first drift; unknown profile exits 2; live-only files are never deleted.
- [x] 3. `scripts/check_agent_profiles.py` refuses a missing directory/SOUL, a skill name that disagrees with its directory, a secret-shaped value, and a SOUL that drops the never-merge rule.
- [x] 4. `make sync-agent-profile PROFILE=<p> [CHECK=1]`, `make check-agent-profiles` and `make agent-profiles-report` carry `##` help lines, are `.PHONY`, and the gate is wired into `ci-unit`.
- [x] 5. `tests/test_agent_profiles.py` has one case per rejection, plus sync→check agreement, the live-only-file rule, the unknown-profile exit code and the repo's own tree passing.
- [x] 6. `.hermes/skills/README.md` states the three-tree split; `docs/BOTS.md` documents the targets.
- [x] 7. `make lint`, `check-docs`, `check-wiring`, `openspec-validate`, `openspec-tasks-check` and `tests/test_agent_profiles.py` pass.
