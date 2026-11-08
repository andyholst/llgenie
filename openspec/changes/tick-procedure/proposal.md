# The orchestrator tick is a procedure, not prose

## Why

The orchestrator tick prompt (job `cc5d2bd4083a`, `$HOME/.hermes/profiles/llgenie-planner/cron/jobs.json`)
was prose: 13 numbered steps of which only 2 named a runnable command (steps 6 and 12). A step a
pass can *satisfy by assertion* is a step that never happened and was reported as done. Measured
2026-11-08, one pass satisfied every step textually and still dispatched three lanes onto new
backlog issues (#2105, #2099, #2156) while 12 of 14 open PRs sat on a stale base and 7 lanes were
idle. Order also drifted: the prompt said "READ 6a FIRST" from step 3, a forward reference that let
a pass do the backlog before the red PRs.

## What changes

1. **`agents/llgenie-planner/tick_board.sh`** (new, executable) — one measurement command that
   prints sections `A.`–`G.` in fixed order (preflight shas, per-PR base/stale/DIRTY, per-lane
   running counts + idle names, queue counts + READY tasks, stalled-worker sweep, CI-at-tip tagged
   TIP/other by headSha, lane-drift CHECK command). Every deterministic figure is printed once under
   a fixed header, so the prompt says "act on section B" and a step either has output here or it
   did not run. `TICK_REPLAY=<dir>` reads recorded fixtures for hermetic tests and historical
   replays.
2. **`agents/llgenie-planner/delegate.sh`** (new, executable) — one dispatch command that proves it
   landed: validates the brief (rejects one missing the `AGENTS:` stamp, the `$HOME` rule, a branch
   or the `BOT <lane> · …` report line), refuses a second vehicle for the same lane+issue, creates
   the task, dispatches, and CONFIRMS by reading the board back — one of `running`,
   `ready (queued on capacity)`, or `BLOCKED`. Message channel mandatory by default (`DO_MSG=1`,
   opt-out `--no-message`); states delegate.sh cannot send the message (message_agent is an agent
   tool) and ends with a `TODO (planner, this turn)` line.
3. **`agents/llgenie-planner/cron/llgenie-orchestrator-tick.md`** (new) — the prompt rewritten as a
   strict ordered procedure (13 steps): every step names the exact command it runs and the output
   line it must quote as evidence. Red PRs (STEP 3) and the board-wide stale-base sweep (STEP 4,
   issue #2158) precede any backlog dispatch (STEP 7); the stalled-worker step (STEP 8, issue
   #2155) is preserved; no forward references.
4. **Drift gate** `make check-tick-prompt` (`scripts/check_tick_prompt.py`) — reds naming both byte
   counts when the live `cron/jobs.json` prompt diverges from the committed copy. Host-only by
   explicit help line (a CI runner has no planner profile or live jobs.json). Issues #2136, #2159.
