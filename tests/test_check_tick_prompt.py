#!/usr/bin/env python3
"""The tick prompt is versioned; the drift gate must prove BOTH directions (issue #2159).

`agents/llgenie-planner/cron/llgenie-orchestrator-tick.md` is the committed source of truth for
the largest instruction in the fleet. `scripts/check_tick_prompt.py` compares the LIVE job's
prompt (`cron/jobs.json`, job `cc5d2bd4083a`) against it and reds when they differ, naming both
byte counts — the same tree-vs-live direction `check_agent_profiles.py` uses for lane files.

A gate is only honest if it PROVES it reds when the bad condition is present, not just that it
greens when clean. These tests drive the real `main()` against fixture jobs.json files:
  * matching prompt -> exit 0 with an `ok:` line;
  * a DIVERGED prompt -> exit 1 with a `FAIL:` line naming BOTH byte counts;
  * a diverged prompt that is only a trailing-newline difference -> still 0 (editors vs JSON
    escaping differ by exactly that; not divergence);
  * no live jobs.json (a CI runner, or a host without the planner profile) -> exit 0 with a
    `note:` line naming why nothing is compared (host-only degradation, never a fake green).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "scripts" / "check_tick_prompt.py"
COMMITTED = REPO / "agents" / "llgenie-planner" / "cron" / "llgenie-orchestrator-tick.md"
JOB = "cc5d2bd4083a"


def _jobs(tmp_path: Path, prompt: str) -> Path:
    jp = tmp_path / "jobs.json"
    jp.write_text(json.dumps({"jobs": [{"id": JOB, "prompt": prompt}]}))
    return jp


def _run(jobs: Path, prompt: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), "check", "--jobs", str(jobs), "--prompt", str(prompt)],
        capture_output=True, text=True, timeout=60)


def test_clean_match_is_green_and_names_both_sizes(tmp_path):
    committed = COMMITTED.read_text(encoding="utf-8")
    jobs = _jobs(tmp_path, committed)
    r = _run(jobs, COMMITTED)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ok:" in r.stdout
    assert str(len(committed.encode())) in r.stdout


def test_diverged_live_prompt_is_red_naming_both_byte_counts(tmp_path):
    committed = COMMITTED.read_text(encoding="utf-8")
    drifted = committed + "\nSTEP N+1 — A NEW ORDER THE LIVE HAS NOT APPLIED.\n"
    jobs = _jobs(tmp_path, drifted)
    r = _run(jobs, COMMITTED)
    assert r.returncode == 1, r.stdout
    assert "FAIL:" in r.stdout
    assert str(len(drifted.encode())) in r.stdout   # the LIVE byte count
    assert str(len(committed.encode())) in r.stdout  # and the COMMITTED byte count
    assert str(JOB) in r.stdout


def test_trailing_newline_difference_is_not_divergence(tmp_path):
    committed = COMMITTED.read_text(encoding="utf-8")
    # JSON transport strips the file's final newline; an editor-written calendar file re-adds it.
    jobs = _jobs(tmp_path, committed.rstrip("\n"))
    r = _run(jobs, COMMITTED)
    assert r.returncode == 0, r.stdout


def test_no_live_jobs_json_is_host_only_not_a_fake_green(tmp_path):
    missing = tmp_path / "no-jobs.json"
    r = _run(missing, COMMITTED)
    assert r.returncode == 0, r.stdout
    assert "note:" in r.stdout and "nothing to compare" in r.stdout


def test_missing_committed_prompt_is_an_invocation_error(tmp_path):
    committed = COMMITTED.read_text(encoding="utf-8")
    jobs = _jobs(tmp_path, committed)
    r = _run(jobs, tmp_path / "does-not-exist.md")
    assert r.returncode == 2, r.stdout
