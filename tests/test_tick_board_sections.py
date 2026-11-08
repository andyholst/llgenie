#!/usr/bin/env python3
"""The tick measurement script is a command, not prose: sections A-G in order (issue #2159).

Until #2159 the orchestrator tick prompt was 13 prose steps of which only 2 named a runnable
command, so any step could be satisfied by assertion. The fix is a single measurement pass —
`agents/llgenie-planner/tick_board.sh` — that prints every deterministic figure under fixed
section headers A..G, so the prompt says "act on section B" and a report that cannot quote the
line it claims to have acted on is a report that step did not happen.

These tests drive the REAL script against a committed replay of the 2026-11-08 board state (the
day the issue measured `stale=12 dirty=2 idle_non_planner=7`), asserting:
  * all seven section headers appear, IN FIXED ORDER A..G;
  * the exact framing of each quoted line (so the prompt's "quote:" targets match);
  * the replay reproduces the issue's measured figures from sections B and C.
The script reads gh/hermes JSON from `TICK_REPLAY` fixtures, so no network and no live board are
needed and the figures are deterministic.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TICK = REPO / "agents" / "llgenie-planner" / "tick_board.sh"
FIX = REPO / "tests" / "fixtures" / "tick" / "replay-2026-11-08"


def _run(repo: Path) -> str:
    env = dict(__import__("os").environ)
    env.update({"HOME": str(repo), "REPO": str(repo),
                "TICK_REPLAY": str(FIX), "NO_FETCH": "1",
                "HERMES_BIN": "/bin/false"})
    return subprocess.run(
        [str(TICK)], capture_output=True, text=True, timeout=60, env=env,
    ).stdout


def _headers(text: str) -> list[str]:
    return [ln for ln in text.splitlines()
            if ln.startswith("===== ") and ln.endswith(" =====")
            and not ln.startswith("===== END")]


def test_all_seven_sections_in_fixed_order_a_to_g(tmp_path):
    (tmp_path / "AGENTS.md").write_text("X" * 91766 + "\n" * (1363 - 0), encoding="utf-8")
    text = _run(tmp_path)
    headers = _headers(text)
    expected = [
        "===== A. PREFLIGHT =====",
        "===== B. OPEN PRs (base vs main, staleness) =====",
        "===== C. LANES (running counts — any 0 is idle and must be given red-PR work) =====",
        "===== D. QUEUE (running / ready / blocked) =====",
        "===== E. STALLED WORKERS + DM WAITERS =====",
        "===== F. CI AT THE TIP (never trust a remembered red) =====",
        "===== G. LANE DRIFT (tree vs live — measure, never sync) =====",
    ]
    assert headers == expected, headers
    assert text.rstrip().endswith("===== END (every step above is a measurement, not a claim) =====")


def test_preflight_reports_the_fixture_main_sha_and_agents_size(tmp_path):
    content = "A" * 91766 + "\n" * 7  # 91773 bytes, 7 lines — sizes must be measured, not guessed
    (tmp_path / "AGENTS.md").write_bytes(content.encode())
    text = _run(tmp_path)
    assert "main_sha: 7ef346c8  (fixture)" in text
    assert f"agents_md: {len(content)}b 7l" in text, "AGENTS.md byte+line count must be printed"


def test_replay_reproduces_the_2026_11_08_measurement(tmp_path):
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    text = _run(tmp_path)
    # The issue's measured state: 14 open PRs, 12 stale, 2 dirty, 7 idle non-planner lanes.
    assert "TOTAL open=14  stale=12  dirty=2" in text, text
    # Section C: idle_non_planner is a lane count — 12 non-planner lanes, 5 running = 7 idle.
    assert "idle_non_planner=7" in text, text
    # The whole point: a report that says "every step done" with stale=12 dirty=2 in front of it
    # is falsifiable — section C must name the idle lanes too.
    assert "  llgenie-tester                     0   <-- IDLE" in text
    assert "  llgenie-status-keeper              0   <-- IDLE" in text


def test_queue_reports_counts_and_names_every_ready_task(tmp_path):
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    text = _run(tmp_path)
    assert "  running   8" in text
    assert "  ready     3" in text
    assert "  blocked   5" in text
    for tid, lane, title in (("t_q0", "llgenie-tester", "ready task 0"),
                             ("t_q1", "llgenie-product-manager", "ready task 1"),
                             ("t_q2", "llgenie-business-analyst", "ready task 2")):
        assert f"READY {tid} {lane}  {title}" in text


def test_ci_at_the_tip_tags_tip_vs_other_by_headsha(tmp_path):
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    text = _run(tmp_path)
    # runs 100/101 have headSha == fixture main_sha -> TIP; the rest are `other`.
    assert "TIP   run=100" in text
    assert "TIP   run=101" in text
    assert "other run=102" in text
    assert "failure   other run=103" in text, "the non-tip red must be tagged `other`, never silently a tip red"


def test_lane_drift_names_the_exact_check1_command(tmp_path):
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=False)
    text = _run(tmp_path)
    assert "make -C " in text and "sync-agent-profile PROFILE=<lane> CHECK=1" in text
    assert "never run it WITHOUT CHECK=1" in text
