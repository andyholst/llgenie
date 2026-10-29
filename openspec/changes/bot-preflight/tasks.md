# Tasks

- [x] `scripts/bot_preflight.py`: fetch, fast-forward-or-refuse, measure, record. Stdlib only.
- [x] `make bot-preflight` with a `## help` line, `CHECK=1` for the verify mode.
- [x] `preflight.txt` carries the sha, the byte size, the line count, the heading digest and the `AGENTS:` line.
- [x] The heading digest survives prose edits and moves when a rule is added (one test each way).
- [x] Refusals tested: dirty tree names its paths; divergence reports ahead/behind and keeps the leg's commit.
- [x] `bot-unattended` SKILL.md states the preflight.
- [x] `docs/BOTS.md` names the target.
- [x] `make check-pr-hygiene` rejects a bot PR body whose `AGENTS:` sha is not an ancestor of both head and base.
- [x] `make check-agent-skills` fails when a leg skill drops the obligation.
