#!/usr/bin/env python3
"""The ci-hf-live workflow obeys the owner's #1002 ask (merge-to-main live-HF pipeline).

The owner (#1002): "the ci pipeline only runs the hf live tests as a separate pipeline that runs
when merged to main branch". Complementing #1000's "they can't be part of ci unit anymore". This
pins the workflow file so compliance can't decay:

- Trigger is merge to `main` (push on branches: [main]) PLUS a nightly schedule + manual dispatch,
  and NEVER a `pull_request:` trigger and never a non-main branch push — live-HF failures are caught
  at main-merge time, never in a PR and never on a feature branch.
- The job runs the bounded liveness gate (make check-model-links LIVE=1 LIMIT=25) BEFORE the seam
  (make test-unit-network), and never the hermetic unit gate — a dead committed link is a named
  message before any live test runs.
- The schedule minute is odd / its own (issue #275).

Hermetic: pure file reads, no network.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "ci-hf-live.yml"


def _text() -> str:
    assert WORKFLOW.exists(), f"ci-hf-live.yml missing at {WORKFLOW}"
    return WORKFLOW.read_text()


def test_ci_hf_live_triggers_on_merge_to_main_not_pr_or_feature_push():
    """#1002: merge-to-main trigger; never a pull_request, never a non-main push."""

    text = _text()

    # It pushes on main (the merge) ...
    assert re.search(r"^  push:\s*$", text, re.M), "ci-hf-live.yml must have a push trigger (merge)"
    # ... restricted to main ONLY: no wildcard, no other branch, no tags (not every branch push)
    m = re.search(r"branches:\s*\[([^\]]*)\]", text)
    assert m, "push must restrict to branches: [main]"
    branches = [b.strip() for b in m.group(1).split(",") if b.strip()]
    assert branches == ["main"], f"push must be main-only, got branches={branches}"
    assert re.search(r"^  tags:", text, re.M) is None, "push must not trigger on tags"
    # ... is manually dispatchable and optionally scheduled
    assert "workflow_dispatch" in text, "ci-hf-live.yml must be manually dispatchable"
    assert re.search(r"^  schedule:", text, re.M), "ci-hf-live.yml may run nightly (owner-OK'd)"
    # Never on a PR
    assert re.search(r"^  pull_request:", text, re.M) is None, \
        "a live-HF test must never gate a pull request (#1000: not in ci-unit/PR)"


def test_ci_hf_live_runs_the_liveness_gate_then_the_seam():
    """The dedicated pipeline first proves the links resolve, then runs the network-owned set."""

    text = _text()
    assert "make check-model-links LIVE=1 LIMIT=25" in text, \
        "the bounded liveness gate must run first (#1000/#1002)"
    assert "make test-unit-network" in text, \
        "the @pytest.mark.network set must run via the seam (#1000)"
    job = text.split("jobs:", 1)[1]
    assert re.search(r"make test-unit(?!-network)", job) is None, \
        "the hermetic unit gate must never run in the live pipeline (#1000)"
    gate = job.index("make check-model-links LIVE=1 LIMIT=25")
    seam = job.index("make test-unit-network")
    assert gate < seam, "a dead link must fail before any live test (named message, not a 404)"


def test_ci_hf_live_schedule_is_an_odd_own_minute():
    """Issue #275: no bot shares a slot; GitHub drops top-of-hour runs, so the minute is odd."""

    m = re.search(r"cron:\s*\"([0-9]+) ([0-9]+) \* \* \*\"", _text())
    assert m, "ci-hf-live.yml must declare a nightly cron"
    assert int(m.group(1)) % 2 == 1, f"ci-hf-live cron minute is not odd (issue #275)"


def test_the_hermetic_unit_gate_never_runs_the_network_set():
    """#1000/#1002: ci-unit stays `-m "not network"`; the seam is the ONLY `-m network` consumer.
    A live-HF test must never silently run inside ci-unit (the owner: "they can't be part of ci
    unit anymore"), and the dedicated pipeline must never run the hermetic unit gate. This pins the
    one-expression boundary at the Makefile/seam level so neither side can drift into the other.
    """

    mk = (REPO / "Makefile").read_text()
    seam = (REPO / "scripts" / "unit_tests.py").read_text()

    # The seam target exists (the workflow depends on it) and selects the network set
    assert re.search(r"^test-unit-network:", mk, re.M), "the seam target must exist"
    assert "--marker" in seam and "network" in seam, \
        "unit_tests.py must expose the --marker network slot (issue #1000)"
    tail = mk.split("test-unit-network:", 1)[1]
    seam_body = tail.split("\n\ntest-unit:", 1)[0]
    assert "--marker network" in seam_body, \
        "the seam must select the network set by marker (issue #1000)"

    # The hermetic gate region (the test-unit target onward) must never select the network set
    hermetic = tail.split("\n\ntest-unit:", 1)[1]
    assert "--marker network" not in hermetic, \
        "ci-unit/test-unit must never select the network set (issue #1000)"




def test_ci_hf_live_is_rostered_not_exempted():
    """The CI lane's admission: a live-HF gate's red must ROUTE to a repair, not be exempted (#349).

    security-scan is exempted because its red is by-design; a live-HF gate's red is a genuine signal
    (a link went down, a model check failed) and must be consumed by run-failure-reactor.yml. So
    ci-hf-live's exact top-level name is a ROSTER ROW in that workflow, and it has NO exemption entry.
    check-workflows fails when the roster name stops matching, so this cannot rot silently.
    """
    reactor = (REPO / ".github" / "workflows" / "run-failure-reactor.yml").read_text()
    assert "ci-hf-live" in reactor,         "ci-hf-live must be a run-failure-reactor roster row (its red routes to a repair)"

    import json
    ex = json.loads((REPO / "tests" / "fixtures" / "workflow-run-exemptions.json").read_text())
    assert all("ci-hf-live" not in k for k in ex.get("workflows", {})),         "ci-hf-live must not be #349-exempted (a sincere signal is not a work item by default)"
