"""Scheduled bots must not all start at the same minute (issues #271, #272, #275).

Two bots firing together compete for the same runners and, worse, can start on the same work at the
same moment. The claim protocol is what actually prevents two bots on one issue (a bot comments
before it starts), but the schedule should not manufacture the collision in the first place: give
every scheduled workflow its OWN minute, spaced far enough apart that a start overlaps as little as
possible, and give every one a concurrency group so a slow run does not overlap its own next tick.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO / ".github" / "workflows"

#: Minutes the bots use. They only have to be DISTINCT: two jobs that share a minute can begin
#: together, and that is the collision issues #271/#272 were.
GRID = (11, 19, 23, 31, 41, 51)

#: Read-only reporters do not compete for agent work, so they may sit off the grid - but they still
#: may not share a minute with a job that does work (the first test covers that).
READ_ONLY = ("queued-alarm.yml",)


def _scheduled() -> list[tuple[str, str, list[int], str]]:
    out = []
    for f in sorted(WORKFLOWS.glob("*.yml")):
        d = yaml.safe_load(f.read_text()) or {}
        on = d.get(True) or d.get("on") or {}
        for entry in on.get("schedule") or []:
            cron = (entry or {}).get("cron") or ""
            g = d.get("concurrency")
            group = g.get("group") if isinstance(g, dict) else g
            minutes = [int(m) for m in cron.split()[0].split(",") if m.isdigit()]
            out.append((f.name, cron, minutes, group or ""))
    return out


def test_no_two_scheduled_workflows_start_at_the_same_minute():
    """The collision issues #271 and #272 were exactly this: two workflows at 5:17, two at 6:23."""
    seen: dict[tuple[int, int], str] = {}
    for name, cron, minutes, _group in _scheduled():
        hh = cron.split()[1]
        for m in minutes:
            key = (m, hh) if hh.isdigit() else (m, -1)
            if key in seen and seen[key] != name:
                raise AssertionError(f"{name} and {seen[key]} both start at {m} ({cron})")
            seen[key] = name


def test_scheduled_jobs_sit_on_the_shared_grid():
    """Every minute in use is one of the agreed slots, and no two jobs anywhere share one."""
    for name, cron, minutes, _group in _scheduled():
        if name in READ_ONLY:
            continue
        for m in minutes:
            assert m in GRID, f"{name} starts at {m} ({cron}), not one of the agreed slots {GRID}"
    # and no minute may appear twice across all of them: that is what a collision is
    seen: dict[int, str] = {}
    for name, cron, minutes, _g in _scheduled():
        for m in minutes:
            if m in seen and seen[m] != name:
                raise AssertionError(f"{name} and {seen[m]} both own minute {m} ({cron})")
            seen[m] = name


def test_every_scheduled_workflow_has_a_concurrency_group():
    """Without one, a run that takes longer than its interval overlaps its own next tick."""
    for name, cron, _minutes, group in _scheduled():
        assert group, f"{name} ({cron}) has no concurrency group"
