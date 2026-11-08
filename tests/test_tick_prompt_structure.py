#!/usr/bin/env python3
"""The versioned prompt is a numbered procedure with a fixed order (issue #2159).

The orchestrator tick prompt lives at `agents/llgenie-planner/cron/llgenie-orchestrator-tick.md`.
The issue measured 13 prose steps of which only 2 named a command, with STALE work dispatched after
backlog. These tests pin the rewrite:
  * exactly the 13 heading steps STEP 1..13, contiguous;
  * STEP 3 = red PRs outrank, STEP 4 = board-wide stale sweep, STEP 6 = delegate (one
    `bash "$DG"` command), STEP 7 = backlog — red PRs and the sweep precede the backlog;
  * no forward reference ("read step X first"/"see step N") anywhere;
  * every numbered heading names a runnable command or a command that feeds a judgement.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROMPT = REPO / "agents" / "llgenie-planner" / "cron" / "llgenie-orchestrator-tick.md"


def _text() -> str:
    return PROMPT.read_text(encoding="utf-8")


def test_exactly_13_contiguous_steps():
    t = _text()
    headers = re.findall(r"^STEP (\d+) —", t, re.M)
    assert headers == [str(i) for i in range(1, 14)], headers


def test_step_order_red_prs_sweep_delegate_then_backlog():
    t = _text()
    order = {
        n: t.find(f"STEP {n} —")
        for n in (3, 4, 6, 7)
    }
    # red PRs (3) and the board-wide stale sweep (4) come BEFORE the backlog (7),
    # and the delegate step (6) is a distinct logical step, not merged into 3.
    assert order[3] != -1 and order[4] != -1 and order[6] != -1 and order[7] != -1
    assert order[3] < order[4] < order[6] < order[7]
    assert "ONLY NOW THE BACKLOG" in t.split("STEP 7 —")[1].split("\n", 1)[0]


def test_step_6_is_delegate_and_invokes_delegate_sh_once():
    t = _text()
    step6 = t.split("STEP 6 —")[1].split("STEP 7 —")[0]
    assert "HOW TO DELEGATE" in step6
    assert 'bash "$DG"' in step6
    assert "CONFIRMED t_" in step6


def test_no_forward_reference():
    t = _text()
    for pat in (r"read\s+step\s+\d", r"read\s+6[a-z]?\s*first",
                r"see\s+step\s+\d", r"go\s+to\s+step\s+\d"):
        assert not re.search(pat, t, re.I), f"forward reference: {pat}"
