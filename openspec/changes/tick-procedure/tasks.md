# tick-procedure — tasks

- [x] `agents/llgenie-planner/tick_board.sh` — sections A–G in fixed order, executable, `bash -n` clean
- [x] `agents/llgenie-planner/delegate.sh` — one-command dispatch, executable, message mandatory by default
- [x] `agents/llgenie-planner/cron/llgenie-orchestrator-tick.md` — 13 ordered steps, no forward refs
- [x] `scripts/check_tick_prompt.py` + `make check-tick-prompt` (.PHONY, BOTS.md) — drift gate
- [x] tests: `tests/test_tick_board_sections.py`, `tests/test_check_tick_prompt.py`,
      `tests/test_delegate.py`, `tests/test_tick_prompt_structure.py`
- [x] fixtures `tests/fixtures/tick/replay-2026-11-08/` reproducing stale=12 dirty=2 idle_non_planner=7
- [x] change-note trio (`agent-wiki/2026-11-08-tick-is-a-procedure-2159.md`,
      `docs/changes.d/2026-11-08-tick-is-a-procedure-2159.md`, its CHANGES.md row)
- [x] `make check-docs` clean, no forward reference in the prompt
