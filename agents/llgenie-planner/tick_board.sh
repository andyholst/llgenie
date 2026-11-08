#!/usr/bin/env bash
# tick_board.sh — ONE measurement pass for the orchestrator tick (issue #2159).
#
# WHY THIS EXISTS
# ---------------
# The tick prompt was prose: 13 numbered steps of which only 2 named a runnable
# command. Every pass interpreted the words differently, and a pass could
# satisfy a step by asserting it ("I measured quiescence") with nothing behind
# the claim. Measured 2026-11-08: a pass dispatched three lanes onto new
# backlog issues while 13 of 14 open PRs sat on stale bases and 7 lanes were
# idle — every step textually satisfied, the board untouched.
#
# The fix is not more words. It is a command per step: this script performs the
# deterministic measurements ONCE and prints them under fixed section headers
# A..G in that fixed order, so the prompt can say "act on section B" instead of
# describing what to look for. A step either has output here or it did not run.
#
# USAGE
#   tick_board.sh            # human report (what the prompt quotes)
#   tick_board.sh --json     # machine report (for follow-up scripting)
#
# ENV (every path is overrideable so the host and the tests share one script)
#   REPO           git checkout whose origin/main is the measured tip
#                  default $HOME/repository/git/llgenie
#   SLUG           GitHub owner/repo slug, default asimov-agent/llgenie
#   HERMES_BIN     the hermes CLI owning the kanban board, default
#                  $HOME/.hermes/hermes-agent/.hermes/bin/hermes
#   STALL_SWEEP    the #2155 stalled-worker sweep (both classes)
#   TICK_REPLAY    a directory of recorded fixtures (prs.json, kanban.json,
#                  runs.json, main-sha, stalls.txt) used by the tests and by a
#                  dry-run of a captured state instead of the live board.
#   NO_FETCH=1     skip the origin/main fetch (TICK_REPLAY implies it)

set -uo pipefail

REPO="${REPO:-$HOME/repository/git/llgenie}"
SLUG="${SLUG:-asimov-agent/llgenie}"
HERMES_BIN="${HERMES_BIN:-$HOME/.hermes/hermes-agent/.hermes/bin/hermes}"
STALL_SWEEP="${STALL_SWEEP:-$HOME/.hermes/profiles/llgenie-planner/cache/scratch/stall_reclaim.sh}"
REPLAY="${TICK_REPLAY:-}"
JSON=0
[ "${1:-}" = "--json" ] && JSON=1

say()   { [ "$JSON" != "1" ] && printf '===== %s =====\n' "$*"; }
pout()  { printf '%s\n' "$*"; }

# ---------------------------------------------------------------------------
# A. PREFLIGHT — the sha for the whole pass. A verdict quoted against a
# remembered sha is a claim about the past: main moves roughly every 26 min.
# ---------------------------------------------------------------------------
say "A. PREFLIGHT"
if [ -n "$REPLAY" ]; then
  MAIN="$(cat "$REPLAY/main-sha" 2>/dev/null | tr -d '[:space:]')"
  MAIN="${MAIN:-UNKNOWN}"
  pout "replay: ${REPLAY}"
  pout "main_sha: ${MAIN}  (fixture)"
  pout "fetched_at_utc: (fixture — no fetch)"
  AB="$(wc -c < "$REPO/AGENTS.md" 2>/dev/null || echo UNKNOWN)"
  AL="$(wc -l < "$REPO/AGENTS.md" 2>/dev/null || echo UNKNOWN)"
else
  if [ "${NO_FETCH:-0}" != "1" ]; then
    git -C "$REPO" fetch origin main -q 2>/dev/null
  fi
  MAIN="$(git -C "$REPO" rev-parse --short origin/main 2>/dev/null)"
  MAIN="${MAIN:-UNKNOWN}"
  pout "main_sha: ${MAIN}"
  pout "fetched_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  AB="$(git -C "$REPO" show origin/main:AGENTS.md 2>/dev/null | wc -c)"
  AL="$(git -C "$REPO" show origin/main:AGENTS.md 2>/dev/null | wc -l)"
fi
pout "agents_md: ${AB}b ${AL}l   <- cite this sha and size in every brief"

# ---------------------------------------------------------------------------
# B. OPEN PRs — every PR: base sha, STALE/fresh vs this tip, DIRTY, head, title.
# A DIRTY PR gets NO CI run at all: it has no log line to quote, so it must be
# dispatched on dirtiness, never on a green/red CI verdict.
# ---------------------------------------------------------------------------
say "B. OPEN PRs (base vs main, staleness)"
if [ -n "$REPLAY" ]; then
  PRS="$(cat "$REPLAY/prs.json" 2>/dev/null)"
else
  PRS="$(gh pr list --repo "$SLUG" --state open --limit 100 \
    --json number,baseRefOid,mergeStateStatus,mergeable,headRefOid,title 2>/dev/null)"
fi
[ -n "$PRS" ] || PRS='[]'
MAIN="$MAIN" PRS="$PRS" python3 -c '
import json, os
try:
    d = json.loads(os.environ["PRS"])
except Exception:
    d = []
main = os.environ.get("MAIN", "")
stale = dirty = 0
for p in d:
    base = (p.get("baseRefOid") or "")[:8]
    st = p.get("mergeStateStatus") or "?"
    is_stale = bool(main) and base != main
    is_dirty = st == "DIRTY"
    stale += is_stale; dirty += is_dirty
    tag = ("STALE " if is_stale else "fresh ") + ("DIRTY" if is_dirty else st)
    num = p.get("number")
    title = p.get("title") or ""
    head = (p.get("headRefOid") or "")[:8]
    print(f"  #{num:<7} {tag:<24} base={base} head={head}  {title[:52]}")
print(f"  TOTAL open={len(d)}  stale={stale}  dirty={dirty}")
'
pout "  A stale base is ONE board-wide sweep, not N tasks. A DIRTY PR has no CI run at all."

# ---------------------------------------------------------------------------
# C. LANES — running count per lane; any 0 (non-planner) is idle and must be
# given red-PR work before any backlog dispatch.
# ---------------------------------------------------------------------------
say "C. LANES (running counts — any 0 is idle and must be given red-PR work)"
if [ -n "$REPLAY" ]; then
  KT="$(cat "$REPLAY/kanban.json" 2>/dev/null)"
else
  KT="$("$HERMES_BIN" kanban list --json 2>/dev/null)"
fi
[ -n "$KT" ] || KT='[]'
lanes='llgenie-planner llgenie-architect llgenie-issse-implementer llgenie-pr-reviever llgenie-ci-pipelines-maintainer llgenie-documentation-maintainer llgenie-engine-improver llgenie-pr-merge-conflict llgenie-security llgenie-tester llgenie-product-manager llgenie-business-analyst llgenie-status-keeper'
KT="$KT" LANES="$lanes" python3 -c '
import json, os, collections
try:
    tasks = json.loads(os.environ["KT"])
except Exception:
    tasks = []
lanes = os.environ["LANES"].split()
counts = collections.Counter(t.get("assignee") for t in tasks if t.get("status") == "running")
idle = []
for l in lanes:
    n = counts.get(l, 0)
    idle_flag = (n == 0 and l != "llgenie-planner")
    if idle_flag: idle.append(l)
    print(f"  {l:34} {n}" + ("   <-- IDLE" if idle_flag else ""))
print(f"  idle_non_planner={len(idle)}")
'
pout "  Every idle lane with an ownable red PR means this pass is NOT finished."

# ---------------------------------------------------------------------------
# D. QUEUE — running/ready/blocked counts and every READY task (id+assignee+title)
# ---------------------------------------------------------------------------
say "D. QUEUE (running / ready / blocked)"
KT="$KT" python3 -c '
import json, os, collections
try:
    tasks = json.loads(os.environ["KT"])
except Exception:
    tasks = []
c = collections.Counter(t.get("status") for t in tasks)
for s in ("running", "ready", "blocked"):
    print(f"  {s:9} {c.get(s, 0)}")
for t in tasks:
    if t.get("status") == "ready":
        tid = t.get("id"); ass = t.get("assignee"); title = t.get("title") or ""
        print(f"    READY {tid} {ass}  {title[:44]}".rstrip())
'

# ---------------------------------------------------------------------------
# E. STALLED WORKERS — the #2155 sweep, both classes (kanban tasks + DM waiters)
# ---------------------------------------------------------------------------
say "E. STALLED WORKERS + DM WAITERS"
if [ -n "$REPLAY" ]; then
  cat "$REPLAY/stalls.txt" 2>/dev/null | sed 's/^/  /' || pout "  (no stall fixture)"
else
  if [ -x "$STALL_SWEEP" ]; then
    bash "$STALL_SWEEP" 2>&1 | tail -5 | sed 's/^/  /'
  else
    pout "  MISSING $STALL_SWEEP — cannot measure stalls"
  fi
fi

# ---------------------------------------------------------------------------
# F. CI AT THE TIP — tag recent runs TIP vs other by headSha == this main sha.
# A failure whose headSha != main is NOT a main-tip red; never quote it as one.
# ---------------------------------------------------------------------------
say "F. CI AT THE TIP (never trust a remembered red)"
if [ -n "$REPLAY" ]; then
  RUNS="$(cat "$REPLAY/runs.json" 2>/dev/null)"
else
  RUNS="$(gh run list --repo "$SLUG" --limit 6 \
    --json databaseId,workflowName,conclusion,status,headSha 2>/dev/null)"
fi
[ -n "$RUNS" ] || RUNS='[]'
MAIN="$MAIN" RUNS="$RUNS" python3 -c '
import json, os
try:
    d = json.loads(os.environ["RUNS"])
except Exception:
    d = []
main = os.environ.get("MAIN", "")
for r in d:
    same = "TIP" if (r.get("headSha") or "")[:8] == main else "other"
    wf = str(r.get("workflowName") or "?")
    st = str(r.get("status") or "?")
    cc = str(r.get("conclusion") or "-")
    rid = r.get("databaseId", "?")
    print(f"  {wf[:34]:34} {st:10} {cc:9} {same:5} run={rid}")
print()
'
pout "  A failure whose headSha != main_sha is NOT a main-tip red; re-read at the tip."

# ---------------------------------------------------------------------------
# G. LANE DRIFT — the exact CHECK=1 command, per lane. Measure only.
# ---------------------------------------------------------------------------
say "G. LANE DRIFT (tree vs live — measure, never sync)"
if [ -d "$REPO" ] && git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  pout "  run: make -C $REPO sync-agent-profile PROFILE=<lane> CHECK=1   (per lane)"
  pout "  never run it WITHOUT CHECK=1: several tree copies are the truncated side (#2084)."
else
  pout "  repo missing"
fi

echo
echo "===== END (every step above is a measurement, not a claim) ====="
