# Tasks

- [x] 1. Proposal + spec for the rebase bot (issue #246).
- [x] 2. `scripts/rebase_bot_sweep.py`: the one-PR decision, the merge-state rule, the marker-based
      daily guard, the cap, and a reason for every pass-over.
- [x] 3. `scripts/rebase_bot.sh`: `rerere` off, the conflict hand-off to the agent, the structural
      checks, and `--force-with-lease` to the PR's own head remote; never merges.
- [x] 4. Makefile: `rebase-bot-sweep`, `rebase-bot`, `rebase-bot-agent` — phony and documented.
- [x] 5. `rebase-bot.yml`: every 6 hours + manual dispatch, one job that always runs (#107),
      owner-guarded, the agent in the agent image.
- [x] 6. Tests: the sweep against a fake `gh`, and the actor against a real scratch repository with
      a conflicting branch and a stub agent (including: no plain force, gates before the push,
      a failed resolution publishes nothing).
- [x] 7. README + agent-wiki + this change.
- [x] 8. Verify: the suite, `make lint`, `make check-wiring`, `openspec-validate NAME=rebase-bot`.
