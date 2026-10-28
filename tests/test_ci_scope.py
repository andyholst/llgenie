"""Which CI stages a diff selects — one class per rule, one case per class (#824).

`ci.yml` runs one pipeline for every change: a docs-only PR queued the same jobs as a change to
`containers/engines/`. The classifier is the decision that makes a stage selectable, and it must be
tested where it can be wrong in four ways:

  * a class that stops matching a path it owns (a `docs/**` file no longer selects `docs`);
  * a wildcard that stops selecting every class — the dangerous direction, because a quiet skip there
    hides a regression in the gate itself;
  * an unmatched path passing silently instead of failing the run;
  * the job table drifting from `ci.yml`'s real job names (measured: #871 deleted the macOS group, so a
    table written for 28 jobs described 14 jobs that no longer exist).

The last one is asserted against the workflow file itself, so the two cannot drift apart again.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import ci_scope as cs  # noqa: E402

CI = REPO / ".github" / "workflows" / "ci.yml"


# ---- one case per class ----------------------------------------------------------

@pytest.mark.parametrize("path,expected", [
    ("docs/ARCHITECTURE.md", "docs"),
    ("agent-wiki/2026-10-28-note.md", "docs"),
    ("openspec/changes/x/proposal.md", "docs"),
    ("CHANGES.md", "docs"),
    (".hermes/skills/issue-implement/SKILL.md", "skills"),
    ("agents/llgenie-planner/SOUL.md", "skills"),
    ("tests/test_worktree_prune.py", "tests"),
    ("data/trending-quant-catalog.json", "data"),
    ("containers/engines/params/llama.cpp.json", "engines"),
    ("skills/engines/strata/SKILL.md", "engines"),
    ("security-reports/sbom.cdx.json", "security"),
    ("renovate.json", "security"),
])
def test_each_class_is_selected_by_a_path_it_owns(path, expected):
    classes, unmatched = cs.classify([path])

    assert unmatched == []
    assert expected in classes, (path, classes)


def test_containers_and_engines_are_distinct_but_overlap():
    # `containers/engines/...` belongs to both: a container change can break an engine image.
    classes, _ = cs.classify(["containers/engines/params/llama.cpp.json"])
    assert {"containers", "engines"} <= set(classes)

    classes, _ = cs.classify(["containers/scanners/grype/Dockerfile"])
    assert "containers" in classes and "engines" not in classes


# ---- wildcards: the dangerous direction ------------------------------------------

@pytest.mark.parametrize("path", [
    "Makefile",
    "tools/Makefile",
    ".github/workflows/ci.yml",
    "scripts/ci_images.py",
    "scripts/engine_bump.py",
    "scripts/check_docs.py",
    "pytest.ini",
    ".gitleaks.toml",
    "renovate.json",
    "AGENTS.md",
])
def test_a_wildcard_path_selects_every_class(path):
    classes, unmatched = cs.classify([path])

    assert unmatched == []
    assert set(classes) == set(cs.CLASSES), (path, classes)
    assert cs.matched_wildcards([path]), path


def test_a_wildcard_wins_even_beside_a_docs_path():
    # The failure that would hurt most: "it is only a markdown change" next to an AGENTS.md edit.
    classes, _ = cs.classify(["docs/ARCHITECTURE.md", "AGENTS.md"])

    assert set(classes) == set(cs.CLASSES)


# ---- an unmatched path is a loud failure ----------------------------------------

def test_a_path_no_class_claims_is_unmatched_not_silently_dropped():
    classes, unmatched = cs.classify(["mystery/new-tree/file.txt"])

    assert classes == []
    assert unmatched == ["mystery/new-tree/file.txt"]


def test_the_cli_exits_non_zero_and_names_the_unmatched_path(capsys):
    rc = cs.main(["--paths", "docs/ARCHITECTURE.md", "mystery/file.txt"])

    err = capsys.readouterr().err
    assert rc == cs.EXIT_UNCLASSIFIED
    assert "mystery/file.txt matches no class" in err


# ---- selection, and the docs-only win -------------------------------------------

def test_a_docs_only_diff_selects_fewer_than_ten_jobs_and_names_what_it_skipped():
    classes, _ = cs.classify(["docs/ARCHITECTURE.md", "CHANGES.md"])
    rows = cs.select(classes)
    selected = [job for job, runs, _ in rows if runs]
    skipped = [(job, why) for job, runs, why in rows if not runs]

    assert classes == ["docs"]
    assert len(selected) < 10, selected
    assert {"guard", "linux/lint", "linux/openspec"} <= set(selected)
    assert "engine-base" in {job for job, _ in skipped}
    # Every skipped row says which class it would have needed — the log states the decision.
    assert all("needs one of" in why for _, why in skipped), skipped


def test_an_engine_change_selects_the_engine_rows_and_the_install_proof():
    classes, _ = cs.classify(["containers/engines/params/strata.json"])
    rows = dict((job, runs) for job, runs, _ in cs.select(classes))

    assert rows["engine-matrix"] and rows["engine-base"] and rows["linux-published"]
    # `scanner-images` keys on `containers`, and `containers/engines/**` IS a containers path, so an
    # engine-params change selects it too — the class granularity #824 specifies. Recorded here rather
    # than silently narrowed: sharpening the rule (scanners only for `containers/scanners/**`) is part
    # (b)'s job, not this classifier's, and a test that asserted the sharper behaviour would be
    # describing a rule the repo does not have.
    assert rows["scanner-images"], "the issue's table selects the scanners for any `containers` change"


def test_the_report_prints_one_class_line_per_class_and_one_verdict_per_job():
    classes, _ = cs.classify(["tests/test_ci_scope.py"])
    rows = cs.select(classes)
    lines = cs.report(classes, rows, ["tests/test_ci_scope.py"], [])

    assert "[ci-scope] class=tests" in lines
    assert sum(1 for line in lines if "[ci-scope] job=" in line) == len(cs.JOBS)
    assert any(line.startswith("[ci-scope] scope: ") for line in lines)


# ---- the table cannot drift from the workflow ------------------------------------

def test_every_job_the_classifier_names_exists_in_ci_yml():
    workflow = yaml.safe_load(CI.read_text())
    real = set(workflow["jobs"])
    named = {job.split("/")[0] for job, _ in cs.JOBS}      # `linux/unit` -> the `linux` job

    missing = named - real
    assert not missing, f"the classifier names jobs ci.yml does not have: {sorted(missing)}"


def test_the_docs_trigger_list_matches_the_docs_class_minus_its_wildcards():
    docs_globs = set(cs.CLASSES["docs"])
    ignore = [p for p in cs.DOCS_TRIGGER_IGNORE if not p.startswith("!")]
    negations = [p[1:] for p in cs.DOCS_TRIGGER_IGNORE if p.startswith("!")]

    # Every ignored glob is a docs glob, and every wildcard that is a docs glob is re-included.
    assert set(ignore) <= docs_globs, set(ignore) - docs_globs
    wildcard_docs = {w for w in cs.WILDCARDS if w in docs_globs}
    assert wildcard_docs <= set(negations), (wildcard_docs, negations)


def test_ci_yml_ignores_exactly_the_docs_trigger_list():
    """The YAML and the classifier are the same decision, so they cannot drift (issue #824)."""
    workflow = yaml.safe_load(CI.read_text())
    on = workflow.get("on") or workflow.get(True)
    declared = on["pull_request"]["paths-ignore"]

    assert declared == list(cs.DOCS_TRIGGER_IGNORE), declared
    # And the push trigger carries NO path filter: `main` must never be under-tested.
    assert "paths-ignore" not in on["push"] and "paths" not in on["push"]


def test_the_scope_workflow_has_no_path_filter_and_runs_the_docs_gates():
    """`scope` is the always-present check: no filter, one job named `scope`, the docs gates inside."""
    path = REPO / ".github" / "workflows" / "scope.yml"
    workflow = yaml.safe_load(path.read_text())
    on = workflow.get("on") or workflow.get(True)

    assert "paths" not in on["pull_request"] and "paths-ignore" not in on["pull_request"], on
    assert list(workflow["jobs"]) == ["scope"], workflow["jobs"]
    runs = " ".join(step.get("run", "") for step in workflow["jobs"]["scope"]["steps"])
    for gate in ("scripts/ci_scope.py", "make ci-lint", "make check-docs", "make check-wiring",
                 "make check-issue-bodies", "make ci-openspec"):
        assert gate in runs, (gate, runs)
    # No new third-party action: the one `uses:` is the same pinned checkout ci.yml uses.
    uses = [step["uses"] for step in workflow["jobs"]["scope"]["steps"] if "uses" in step]
    assert uses == ["actions/checkout@11d5960a326750d5838078e36cf38b85af677262"], uses

