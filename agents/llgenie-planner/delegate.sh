#!/usr/bin/env bash
# delegate.sh — ONE dispatch, mechanically, and prove it landed (issue #2159).
#
# WHY THIS EXISTS
# ---------------
# "Dispatch it out loud" was prose in the tick prompt, so a pass could report a
# delegation that never happened. Measured 2026-11-08: a pass reported 8 lanes
# "running" while 7 were idle and 12 of 14 PRs sat stale — every dispatch step
# textually satisfied, nothing created.
#
# A dispatch is four things and all four are required:
#   1. a brief on disk (multi-line; inline heredocs get mangled by the caller)
#   2. a kanban task assigned to the owning lane
#   3. a dispatch that actually spawns it
#   4. a confirmation read back from the board   <- this is the only proof
#
# `Spawned: 0` from `kanban dispatch` is NOT a failure: it means capacity is
# full and the task is queued `ready`. That is a different state from running
# and must be reported as such — conflating the two is how an idle board reads
# busy. A `ready (queued)` task is a normal outcome, never a red.
#
# USAGE
#   delegate.sh --lane <lane> --issue <n> --brief <file>
#               [--title T] [--max-runtime N] [--no-message] [--dry-run]
#
#   --no-message  opt out of the message channel. Default is MANDATORY (DO_MSG=1):
#                 the message makes the lane act in its thread while the task only
#                 survives turns, so a lane that received neither must not be
#                 counted busy. A task created without --no-message ends with a
#                 `TODO (planner, this turn)` line the planner must act on.
#   --dry-run   validate the brief and print the exact commands; create nothing
#
# LIMIT: delegate.sh CANNOT send the message itself. message_agent is an agent
# tool, not a shell command, so delivery stays in the planner's turn: the output
# ends with a `TODO (planner, this turn)` line naming the task id to quote.
#
# EXIT
#   0  task exists and is running, or queued `ready` (capacity), or already delegated
#   2  bad usage / missing brief / task created but could not be confirmed
#
# ENV
#   HERMES_BIN  the hermes CLI, default $HOME/.hermes/hermes-agent/.hermes/bin/hermes

set -uo pipefail

HERMES_BIN="${HERMES_BIN:-$HOME/.hermes/hermes-agent/.hermes/bin/hermes}"
LANE=""; ISSUE=""; BRIEF=""; TITLE=""; MAXRT=5400; DO_MSG=1; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --lane) LANE="${2:-}"; shift 2;;
    --issue) ISSUE="${2:-}"; shift 2;;
    --brief) BRIEF="${2:-}"; shift 2;;
    --title) TITLE="${2:-}"; shift 2;;
    --max-runtime) MAXRT="${2:-}"; shift 2;;
    --message) DO_MSG=1; shift;;  # compat: message is the default now
    --no-message) DO_MSG=0; shift;;
    --dry-run) DRY=1; shift;;
    *) echo "delegate: unknown argument '$1'" >&2; exit 2;;
  esac
done

say() { printf '[delegate] %s\n' "$*"; }

[ -n "$LANE" ]  || { say "FATAL: --lane required"; exit 2; }
[ -n "$ISSUE" ] || { say "FATAL: --issue required"; exit 2; }
case "$ISSUE" in ''|*[!0-9]*) say "FATAL: --issue must be a number, got '$ISSUE'"; exit 2;; esac
[ -f "$BRIEF" ] || { say "FATAL: brief not found: ${BRIEF:-<empty>}"; exit 2; }

# --- gate 1: the brief must carry the things a lane cannot invent -----------
# A brief lacking any of these produces a PR that reds its own gates, so the
# dispatch REFUSES it rather than sends a doomed lane into a doomed workflow.
missing=""
grep -q 'AGENTS:'    "$BRIEF" || missing="$missing AGENTS-stamp"
grep -qi '\$HOME'    "$BRIEF" || missing="$missing HOME-rule"
grep -qi 'branch'    "$BRIEF" || missing="$missing branch"
grep -q 'BOT '       "$BRIEF" || missing="$missing report-line"
if [ -n "$missing" ]; then
  say "FATAL: brief is incomplete — missing:$missing"
  say "       (a brief without these produces a PR that reds its own gates)"
  exit 2
fi

TITLE="${TITLE:-$LANE #$ISSUE: $(head -1 "$BRIEF" | cut -c1-70)}"

# --- gate 2: one vehicle per issue ------------------------------------------
if [ "$DRY" != "1" ]; then
  existing="$("$HERMES_BIN" kanban list --json 2>/dev/null \
    | python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception: d=[]
for t in d:
    if t.get('status') in ('running','ready') and '$LANE' in (t.get('assignee') or '') and '#$ISSUE' in (t.get('title') or ''):
        print(t['id'], t['status']); break
" 2>/dev/null)"
  if [ -n "$existing" ]; then
    say "ALREADY DELEGATED: $existing — not creating a second vehicle for #$ISSUE"
    echo "$existing"
    exit 0
  fi
fi

if [ "$DRY" = "1" ]; then
  say "DRY RUN — would run:"
  say "  $HERMES_BIN kanban create \"$TITLE\" --body-file $BRIEF --assignee $LANE --max-runtime $MAXRT --created-by llgenie-planner"
  say "  $HERMES_BIN kanban dispatch"
  [ "$DO_MSG" = "1" ] && say "  message_agent -> $LANE (same brief)"
  say "brief OK: $(wc -c < "$BRIEF")b, carries AGENTS/, \$HOME, branch, report line"
  exit 0
fi

# --- 1+2: create ------------------------------------------------------------
out="$("$HERMES_BIN" kanban create "$TITLE" --body-file "$BRIEF" \
        --assignee "$LANE" --max-runtime "$MAXRT" --created-by llgenie-planner 2>&1)"
say "$out" | tail -1
TASK="$(printf '%s' "$out" | grep -oE 't_[a-z0-9]+' | head -1)"
[ -n "$TASK" ] || { say "FATAL: no task id in create output"; exit 2; }

# --- 3: dispatch ------------------------------------------------------------
dout="$("$HERMES_BIN" kanban dispatch 2>&1)"
spawned="$(printf '%s' "$dout" | grep -oE 'Spawned:[[:space:]]+[0-9]+' | grep -oE '[0-9]+$' | head -1)"
spawned="${spawned:-0}"

# --- 4: CONFIRM from the board — the only proof -----------------------------
status="$("$HERMES_BIN" kanban list --json 2>/dev/null | python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception: d=[]
for t in d:
    if t['id']=='$TASK': print(t['status']); break
" 2>/dev/null)"

case "$status" in
  running) say "CONFIRMED $TASK running -> $LANE" ;;
  ready)   say "CONFIRMED $TASK ready (queued on capacity — spawned=$spawned, all slots busy)" ;;
  blocked) say "CONFIRMED $TASK BLOCKED — it will not run until unblocked"; echo "$TASK blocked"; exit 0 ;;
  "")      say "FATAL: $TASK not found on the board after create"; exit 2 ;;
  *)       say "CONFIRMED $TASK $status" ;;
esac

# --- message channel --------------------------------------------------------
# delegate.sh CANNOT send the message: message_agent is an agent tool, not a
# shell command, so delivery stays in the planner's turn. The pass is only
# complete when the planner acts on the TODO line below and the lane's own
# thread carries the brief.
if [ "$DO_MSG" = "1" ]; then
  say "STATUS: the message channel is part of this dispatch (DO_MSG=1, mandatory by default)."
  say "  delegate.sh cannot send it — message_agent is an agent tool, not a shell command."
  say "  TODO (planner, this turn): message_agent -> $LANE quoting task id $TASK and the brief."
else
  say "STATUS: message channel opted out (--no-message)."
  say "  NOTE: the task exists but the lane was NOT told in its own thread. Do NOT count it busy."
fi

echo "$TASK $status"
