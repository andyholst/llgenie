# 2026-11-08 — the tick is a procedure, not prose (issue #2159)

## Problem

The orchestrator tick prompt (job `cc5d2bd4083a`, `cron/jobs.json`) was prose: 13 numbered steps
of which only 2 named a runnable command (steps 6 and 12; census reproducible by splitting on
`^\s*(\d+)\.\s+` and counting indented command-shaped lines per step). Any step could therefore be
*satisfied by assertion* — a pass could report "measured quiescence" with no output behind the
word. Measured 2026-11-08 on the same day: a pass satisfied every step textually and still
dispatched three lanes onto new backlog issues (#2105, #2099, #2156) while 12 of 14 open PRs sat
on a stale base and 7 lanes were idle. Order also drifted: the prompt told step 3 to "READ 6a
FIRST", a forward reference that let a pass do the backlog before the red PRs.

## The fix — one measurement, one ordered procedure

1. **`tick_board.sh`** (versioned at `agents/llgenie-planner/tick_board.sh`, executable) performs
   every deterministic measurement ONCE and prints it under fixed section headers `A.`–`G.` in
   that order: A preflight (fetched origin/main sha + UTC fetch time + AGENTS.md bytes/lines),
   B open PRs (base sha, STALE/fresh vs the tip, DIRTY, head, title + `stale=`/`dirty=` totals),
   C lanes (running count per lane, idle lanes named, `idle_non_planner=N`), D queue
   (running/ready/blocked + every READY task by id/assignee/title), E stalled workers (both
   classes), F CI at the tip (each recent run tagged `TIP`/`other` by headSha vs the fetched sha),
   G lane drift (the exact `make sync-agent-profile PROFILE=<lane> CHECK=1` command). A section
   with no output means that step did not run. `TICK_REPLAY=<dir>` reads recorded fixtures so the
   historical board state is reproducible in tests and dry runs instead of a live board.

2. **`delegate.sh`** (versioned at `agents/llgenie-planner/delegate.sh`, executable) makes a
   dispatch one command that proves it landed: it validates the brief (rejects one missing the
   `AGENTS:` stamp, the `$HOME` rule, a branch or the `BOT <lane> · …` report line), refuses a
   second vehicle for the same lane+issue (`ALREADY DELEGATED: t_xxxx <status>`), creates the
   task, dispatches, and CONFIRMS by reading the board back — stating exactly one of `running`,
   `ready (queued on capacity)`, or `BLOCKED`. The message channel is mandatory by default
   (`DO_MSG=1`, opt-out `--no-message`); delegate.sh states it cannot send the message itself
   (message_agent is an agent tool, not a shell command) and its output ends with a
   `TODO (planner, this turn)` line the pass must act on by sending the brief in its own thread.

3. **The prompt is now a strict ordered procedure** (versioned at
   `agents/llgenie-planner/cron/llgenie-orchestrator-tick.md`), read top to bottom with no forward
   references: every step names the exact command it runs *and* the output line it must quote as
   evidence. Red PRs and the board-wide stale-base sweep (issue #2158) come before any backlog
   dispatch; the stalled-worker step (#2155) is preserved as step 7.

4. **The drift gate** `make check-tick-prompt` (`scripts/check_tick_prompt.py`) reds when the
   live `cron/jobs.json` prompt diverges from the committed copy, naming BOTH byte counts — the
   tree-vs-live direction `check_agent_profiles.py` already uses for lane files (issues #2136,
   #2159). Host-only by explicit help line (`make check-tick-prompt` says it: a CI runner has no
   planner profile or live jobs.json), so it needs no host-only-wiring entry.

## Verified

- `tick_board.sh` is `bash -n` clean and produced all seven sections live; a committed replay of
  the 2026-11-08 board state reproduces `stale=12`, `dirty=2`, `idle_non_planner=7` from sections
  B and C.
- `tests/test_tick_board_sections.py`, `tests/test_check_tick_prompt.py`, `tests/test_delegate.py`
  (17 tests) pass in the `llgenie/test` container, and the drift gate provably reds on divergence
  (both byte counts named) and greens on equality.
- The live tick prompt has not been edited here; the planner applies the committed copy via the
  #2136 mechanism, which closes the drift.
