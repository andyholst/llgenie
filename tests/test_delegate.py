#!/usr/bin/env python3
"""delegate.sh is one dispatch command that PROVES it landed (issue #2159).

The tick prompt's dispatch step was prose ("dispatch it out loud"), so a pass could report a
delegation that never happened — measured 2026-11-08: a pass reported 8 lanes running while 7
were idle and 12 of 14 PRs sat stale. delegate.sh makes the dispatch mechanical and verifiable:
it validates the brief, refuses a second vehicle, creates the task, dispatches, and CONFIRMS by
reading the board back. The claim that survives is ONLY the `CONFIRMED t_xxxx <status>` line.

These tests drive the REAL script with a fake HERMES_BIN (a tiny stub that answers `kanban
list/create/dispatch`) and assert each gate independently:
  * a brief missing AGENTS:/$HOME/branch/BOT is REJECTED, naming them;
  * a missing brief file is rejected;
  * an existing running/ready task for the same lane+issue is refused (ALREADY DELEGATED);
  * the three confirmation states print the exact distinction — running vs
    `ready (queued on capacity)` vs BLOCKED — so a queued task is never reported as running.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DELEGATE = REPO / "agents" / "llgenie-planner" / "delegate.sh"


def _fake_hermes(tmp_path: Path, board: list[dict], spawn: int = 1,
                 create_out: str = "Created t_deadbeef", first_empty: bool = True) -> Path:
    """A stub `hermes` answering kanban list/create/dispatch from a fixture board.

    By default the first `list --json` (the pre-create duplicate check) answers EMPTY so the
    create path is exercised, and every later `list --json` (the confirmation read-back)
    answers `board`. Pass `first_empty=False` when the duplicate-vehicle gate is the target —
    then the first list already carries the existing task and delegate refuses before creating.
    """
    binp = tmp_path / "bin"
    binp.mkdir(exist_ok=True)
    script = binp / "hermes"
    board_json = json.dumps(board)
    first = "echo '[]'" if first_empty else "echo \"$BOARD\""
    script.write_text(
        "#!/bin/bash\n"
        f"BOARD='{board_json}'\n"
        f"SPAWN='{spawn}'\n"
        f"CREATE_OUT='{create_out}'\n"
        f"CNT='{binp}/cnt'\n"
        "if [ \"$2\" = \"list\" ] && [ \"$3\" = \"--json\" ]; then\n"
        "  n=$(cat \"$CNT\" 2>/dev/null || echo 0); n=$((n+1)); echo $n > \"$CNT\"\n"
        f"  if [ \"$n\" -eq 1 ]; then {first}; else echo \"$BOARD\"; fi\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$2\" = \"create\" ]; then echo \"$CREATE_OUT\"; exit 0; fi\n"
        "if [ \"$2\" = \"dispatch\" ]; then echo \"Spawned: $SPAWN\"; exit 0; fi\n"
        "exit 1\n")
    script.chmod(0o755)
    return binp / "hermes"


def _brief(tmp_path: Path, name: str = "brief.md", complete: bool = True) -> Path:
    p = tmp_path / name
    body = (
        "# implement #123\n\n"
        "AGENTS: sha bytes lines\n"
        "use $HOME not /home/asimov\n"
        "branch fix/123\n"
        "open with:\n"
        "BOT llgenie-test-lane · working on #123 · branch fix/123 · blocked on none · next edit\n")
    if not complete:
        body = (body.replace("AGENTS: ", "MISSING: ")
                .replace("$HOME", "/home/asimov")
                .replace("branch fix/123", "x")
                .replace("BOT llgenie-test-lane", "Just a lane"))
    p.write_text(body)
    return p


def _run(hermes: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(__import__("os").environ)
    env["HERMES_BIN"] = str(hermes)
    return subprocess.run([str(DELEGATE), "--lane", "llgenie-test-lane", "--issue", "123",
                           "--brief", args[0], *args[1:]],
                          capture_output=True, text=True, timeout=60,
                          env=env)


def test_incomplete_brief_is_rejected_naming_the_missing_items(tmp_path):
    hermes = _fake_hermes(tmp_path, [])
    brief = _brief(tmp_path, complete=False)
    r = _run(hermes, str(brief))
    assert r.returncode != 0, r.stdout + r.stderr
    assert "brief is incomplete" in r.stdout
    for item in ("AGENTS-stamp", "HOME-rule", "branch", "report-line"):
        assert item in r.stdout


def test_missing_brief_file_is_rejected(tmp_path):
    hermes = _fake_hermes(tmp_path, [])
    r = _run(hermes, str(tmp_path / "no-such-brief.md"))
    assert r.returncode != 0
    assert "brief not found" in r.stdout


def test_second_vehicle_for_the_same_lane_issue_is_refused(tmp_path):
    board = [{"id": "t_existing", "title": "llgenie-test-lane #123: some task",
              "assignee": "llgenie-test-lane", "status": "running"}]
    hermes = _fake_hermes(tmp_path, board, first_empty=False)
    brief = _brief(tmp_path)
    r = _run(hermes, str(brief))
    assert r.returncode == 0
    assert "ALREADY DELEGATED: t_existing running" in r.stdout


def test_confirmed_running_is_reported_as_running(tmp_path):
    board = [{"id": "t_deadbeef", "title": "llgenie-test-lane #123: task",
              "assignee": "llgenie-test-lane", "status": "running"}]
    hermes = _fake_hermes(tmp_path, board)
    brief = _brief(tmp_path)
    r = _run(hermes, str(brief))
    assert r.returncode == 0
    assert "CONFIRMED t_deadbeef running -> llgenie-test-lane" in r.stdout


def test_queued_ready_is_never_reported_as_running(tmp_path):
    board = [{"id": "t_deadbeef", "title": "llgenie-test-lane #123: task",
              "assignee": "llgenie-test-lane", "status": "ready"}]
    hermes = _fake_hermes(tmp_path, board, spawn=0)
    brief = _brief(tmp_path)
    r = _run(hermes, str(brief))
    assert r.returncode == 0
    assert "CONFIRMED t_deadbeef ready (queued on capacity" in r.stdout
    assert "running" not in r.stdout


def test_blocked_task_reports_blocked(tmp_path):
    board = [{"id": "t_deadbeef", "title": "llgenie-test-lane #123: task",
              "assignee": "llgenie-test-lane", "status": "blocked"}]
    hermes = _fake_hermes(tmp_path, board)
    brief = _brief(tmp_path)
    r = _run(hermes, str(brief))
    assert r.returncode == 0
    assert "CONFIRMED t_deadbeef BLOCKED — it will not run until unblocked" in r.stdout


def test_message_channel_is_mandatory_by_default_and_ends_in_todo(tmp_path):
    # AC #2159: DO_MSG=1 by default, the output states delegate.sh cannot send
    # the message itself (message_agent is an agent tool, not a shell command),
    # and ends with a `TODO (planner, this turn)` line naming the task id.
    board = [{"id": "t_deadbeef", "title": "llgenie-test-lane #123: task",
              "assignee": "llgenie-test-lane", "status": "running"}]
    hermes = _fake_hermes(tmp_path, board)
    brief = _brief(tmp_path)
    r = _run(hermes, str(brief))   # no flags at all
    assert r.returncode == 0
    assert "CONFIRMED t_deadbeef running -> llgenie-test-lane" in r.stdout
    assert "DO_MSG=1" in r.stdout
    assert "message_agent is an agent tool" in r.stdout
    assert "TODO (planner, this turn)" in r.stdout
    assert "t_deadbeef" in r.stdout.split("TODO (planner, this turn)")[1]  # the line names the task


def test_no_message_opt_out_only_email_never_silent(tmp_path):
    # --no-message opts out, but the output must still warn the lane was NOT
    # told in its thread, so a lane that got no message is never counted busy.
    board = [{"id": "t_deadbeef", "title": "llgenie-test-lane #123: task",
              "assignee": "llgenie-test-lane", "status": "running"}]
    hermes = _fake_hermes(tmp_path, board)
    brief = _brief(tmp_path)
    r = _run(hermes, str(brief), "--no-message")
    assert r.returncode == 0
    assert "CONFIRMED t_deadbeef running" in r.stdout
    assert "NOT told in its own thread" in r.stdout
    assert "TODO (planner, this turn)" not in r.stdout
