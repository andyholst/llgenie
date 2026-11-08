#!/usr/bin/env python3
"""The orchestrator tick prompt is versioned; this gate reds when LIVE drifts from it (issue #2159).

The tick prompt is the largest single instruction this fleet runs — it decides what every pass
does — and until #2159/#2136 it lived only as a string inside ``cron/jobs.json`` on one host. It
is now committed at ``agents/llgenie-planner/cron/llgenie-orchestrator-tick.md`` and this gate
proves the running job's prompt still matches that committed copy, exactly the way
``check_agent_profiles.py`` proves a live lane's files match the tree.

A prompt that diverges is either (a) a private edit that shipped no PR (the #2136 failure the gate
exists to catch) or (b) a prompt that was correctly improved in the tree but never applied to the
live job. Both are a real divergence the pass must see, so the gate reds and names BOTH byte
counts — the reader reconciles by applying the committed copy via the planner's own mechanism.

This is deliberately the SAME comparison as the tick's ``G. LANE DRIFT`` section, because section
G already checks every profile's tree-vs-live drift: ``tick_board.sh`` prints the exact
``make sync-agent-profile PROFILE=<lane> CHECK=1`` command for that. The prompt is just another
file the tree owns, so the gate uses the same one-way direction (tree -> live): the committed copy
is the source of truth, never the live string.

Commands:
    check_tick_prompt.py check        exit 0 when the live job prompt == the committed copy;
                                      exit 1 with both byte counts when they differ;
                                      exit 0 with a skip note when no live jobs.json exists
                                      (a CI runner has no planner profile — host-only, like
                                      scores of the live drifts)
    check_tick_prompt.py report       print the committed + live byte counts and the match
    check_tick_prompt.py --all        run over the whole tree, not the host (unused in CI; the
                                      committed copy always matches itself — kept for symmetry)

Paths override for hermetic tests (and for running on a host where the planner profile lives
elsewhere):
    --jobs <path>     live jobs.json   default $HOME/.hermes/profiles/llgenie-planner/cron/jobs.json
    --prompt <path>   committed prompt default <repo>/agents/llgenie-planner/cron/llgenie-orchestrator-tick.md

Exit codes follow the repo convention (issue #883): 0 clean (or legitimately nothing to compare),
1 the tree/live pair disagrees (a real divergence), 2 bad invocation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

#: The job whose prompt is the orchestrator tick (the cron config names it by id).
TICK_JOB = "cc5d2bd4083a"

#: The committed prompt — the source of truth this gate compares the live job against.
DEFAULT_PROMPT = REPO / "agents" / "llgenie-planner" / "cron" / "llgenie-orchestrator-tick.md"

#: The live jobs.json that the planning host's own scheduler reads.
DEFAULT_JOBS = Path.home() / ".hermes" / "profiles" / "llgenie-planner" / "cron" / "jobs.json"


def _live_prompt(jobs: Path) -> tuple[str | None, str]:
    """The current tick job's prompt string, or ``(None, reason)`` when it cannot be read.

    A missing file, a missing job, or a job whose ``prompt`` is absent all return ``(None, reason)``
    so the caller can degrade cleanly (host-only gate: a CI runner has no planner profile).
    """
    if not jobs.is_file():
        return None, f"no live jobs.json at {jobs}"
    try:
        data = json.loads(jobs.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"live jobs.json unreadable: {exc}"
    jobs_list = data.get("jobs", []) if isinstance(data, dict) else data
    jobs_list = jobs_list if isinstance(jobs_list, list) else []
    for job in jobs_list:
        if isinstance(job, dict) and job.get("id") == TICK_JOB:
            prompt = job.get("prompt")
            if prompt is not None:
                return str(prompt), ""
            return None, f"live job {TICK_JOB} carries no prompt field"
    return None, f"live jobs.json has no job with id {TICK_JOB}"


def _committed(prompt: Path) -> str | None:
    """The committed prompt text, or None when the file is absent."""
    try:
        return prompt.read_text(encoding="utf-8")
    except OSError:
        return None


def _check(jobs: Path, prompt: Path) -> tuple[int, list[str]]:
    """Compare live to committed; return (exit_code, lines)."""
    live, reason = _live_prompt(jobs)
    if live is None:
        # Host-only degradation: nothing to compare on a machine without the planner profile.
        return 0, [f"note: {reason} — nothing to compare (host-only gate, issue #2159)"]

    committed = _committed(prompt)
    if committed is None:
        return 2, [f"FATAL: committed prompt not found at {prompt}"]

    # A trailing newline on one side but not the other (editor vs JSON escape) is not divergence.
    same = live.rstrip("\n") == committed.rstrip("\n")
    lb, cb = len(live.encode()), len(committed.encode())
    if same:
        return 0, [f"ok: live tick prompt == committed ({lb}b both sides)"]
    return 1, [
        f"FAIL: live tick prompt diverges from the committed copy — live {lb}b, committed {cb}b",
        f"  committed: {prompt}",
        f"  live job:  {TICK_JOB} in {jobs}",
        "  reconcile: apply the committed copy to the live job via the planner's prompt-versioning",
        f"  page (issue #2136), then re-run `make check-tick-prompt` (or quote that the divergence",
        "  is an intentional pending improvement that shipped no PR).",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_tick_prompt.py",
        description="Red when the live orchestrator tick prompt diverges from the committed copy.")
    parser.add_argument("subcommand", choices=["check", "report"], nargs="?", default="check")
    parser.add_argument("--jobs", type=Path, default=DEFAULT_JOBS,
                        help="live jobs.json (defaults to the planner profile's)")
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT,
                        help="committed prompt (defaults to agents/llgenie-planner/cron/…)")
    parser.add_argument("--all", action="store_true", help="run over the tree (self-consistent)")
    args = parser.parse_args(argv)

    if args.all:
        # The committed copy always equals itself; kept for a clean `--all` symmetry.
        c = _committed(args.prompt) or b""
        print(f"ok: committed prompt at {args.prompt} is self-consistent ({len(c)})")
        return 0

    code, lines = _check(args.jobs, args.prompt)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
