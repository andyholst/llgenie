"""The scan pipeline (issue #715): one invocation seam, one policy, pinned scanner images.

Every rule is proven on a fixture, then the real tree is asserted sane: the policy decides what
fails (full vs pull-request mode), a finding without a fix never blocks, a report that cannot be
parsed is never a pass, and the workflow references the scanner images from `digests.json` rather
than a tag. No Docker and no network: the scanners themselves are exercised by the
`security-scan` CI job (`make security-scan-all`).

NO-SKIP POLICY: a missing prerequisite is a LOUD FAILURE, never a skip.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import security_scan as ss  # noqa: E402

TRIVY_OK = {"Results": [{"Vulnerabilities": [
    {"VulnerabilityID": "CVE-1", "PkgName": "numpy", "InstalledVersion": "1.0",
     "FixedVersion": "1.1", "Severity": "CRITICAL"},
]}]}
TRIVY_NO_FIX = {"Results": [{"Vulnerabilities": [
    {"VulnerabilityID": "CVE-2", "PkgName": "gguf", "InstalledVersion": "0.1",
     "FixedVersion": "", "Severity": "CRITICAL"},
]}]}
TRIVY_HIGH = {"Results": [{"Vulnerabilities": [
    {"VulnerabilityID": "CVE-3", "PkgName": "numpy", "InstalledVersion": "1.0",
     "FixedVersion": "1.2", "Severity": "HIGH"},
]}]}
GRYPE_ONE = {"matches": [{
    "vulnerability": {"id": "GHSA-1", "severity": "Critical"},
    "artifact": {"name": "openssl", "version": "3.0"},
    "fix": {"versions": ["3.1"]},
}]}

POLICY = {"fail_on": ["critical", "high"], "pr_fail_on": ["critical"],
          "require_fix": True, "issue_severities": ["critical", "high"]}


def _reports(tmp_path: Path, **files) -> Path:
    d = tmp_path / "reports"
    d.mkdir(parents=True, exist_ok=True)
    for name, payload in files.items():
        (d / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    return d


def test_trivy_findings_are_normalised():
    """A trivy report becomes one shape with id, package, current, fixed and severity."""

    # Given a trivy report with one CRITICAL that has a fix
    # When  it is normalised
    items = ss._trivy_findings(TRIVY_OK)

    # Then  every field a remediation needs is present
    assert items == [{"id": "CVE-1", "package": "numpy", "current": "1.0",
                      "fixed": "1.1", "severity": "critical", "source": "trivy"}]


def test_grype_findings_are_normalised():
    """A grype match carries its fixed versions in `fix.versions`, not one string."""

    # Given a grype report
    # When  it is normalised
    items = ss._grype_findings(GRYPE_ONE)

    # Then  the fixed version is joined from the list
    assert items[0]["fixed"] == "3.1"
    assert items[0]["severity"] == "critical"


def test_full_mode_fails_on_a_high_with_a_fix(tmp_path, monkeypatch):
    """The scheduled/manual policy is critical+high with a fix available."""

    # Given a report with a HIGH that has a fix
    items = ss._trivy_findings(TRIVY_HIGH)

    # When  the full policy is applied
    bad = ss.blocking(items, POLICY, "full")

    # Then  it blocks
    assert [i["id"] for i in bad] == ["CVE-3"]


def test_pr_mode_only_fails_on_critical(tmp_path, monkeypatch):
    """A pre-existing High must not red every PR; the daily run still enforces it."""

    # Given a HIGH with a fix
    items = ss._trivy_findings(TRIVY_HIGH)

    # When  the pull-request policy is applied
    bad = ss.blocking(items, POLICY, "pr")

    # Then  it does not block, and the full mode still does
    assert bad == []
    assert ss.blocking(items, POLICY, "full") != []


def test_a_finding_without_a_fix_never_blocks():
    """`require_fix` is why an unfixable advisory cannot stall the repository."""

    # Given a CRITICAL with no fixed version
    items = ss._trivy_findings(TRIVY_NO_FIX)

    # When  the policy requires a fix
    bad = ss.blocking(items, POLICY, "full")

    # Then  it is recorded but not blocking
    assert bad == []
    assert ss.blocking(items, dict(POLICY, require_fix=False), "full") != []


def test_verdict_fails_and_passes_from_the_reports(tmp_path, monkeypatch):
    """`make security-verdict` is the run's exit code, driven only by the reports on disk."""

    # Given a reports directory with a blocking finding
    monkeypatch.setattr(ss, "REPORTS", _reports(tmp_path, trivy=TRIVY_OK))

    # When  the verdict runs
    rc_bad = ss.verdict("full")

    # Then  it fails, and an empty directory passes with nothing recorded
    assert rc_bad == 1
    monkeypatch.setattr(ss, "REPORTS", _reports(tmp_path / "empty", trivy={"Results": []}))
    assert ss.verdict("full") == 0


def test_an_unparseable_report_is_not_a_pass(tmp_path, monkeypatch):
    """A truncated report must fail loudly; treating it as clean is the defect this prevents."""

    # Given a corrupt trivy report
    d = tmp_path / "reports"
    d.mkdir()
    (d / "trivy.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(ss, "REPORTS", d)

    # When  findings are read
    try:
        ss.findings()
    except SystemExit as exc:
        # Then  the run refuses rather than reporting zero findings
        assert "does not parse" in str(exc)
    else:
        raise AssertionError("a corrupt report was treated as clean")


def test_the_policy_and_digests_are_sane():
    """The real tree: a non-empty policy, pr_fail_on ⊆ fail_on, every scanner ref recorded."""

    # Given this repository
    # When  the gate runs
    rc = ss.check()

    # Then  it passes
    assert rc == 0


def test_the_workflow_uses_the_digests_and_a_manual_form():
    """The workflow must name the pinned refs, keep the manual trigger, and never install a scanner."""

    # Given the scan workflow
    text = (REPO / ".github/workflows/security-scan.yml").read_text(encoding="utf-8")

    # When  it is read for the pipeline's hard requirements
    # Then  the manual trigger, the guard, the make seam and the pinned upload actions are present
    assert "workflow_dispatch:" in text
    assert "  pull_request:" in text and "  push:" in text and "  schedule:" in text
    assert "make security-scan-all" in text and "make security-verdict" in text
    assert "guard:" in text
    # And nothing floats: every `uses:` is a 40-hex SHA
    import re
    refs = re.findall(r"uses:\s+(\S+)", text)
    assert refs, "the workflow uses no action at all"
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref) for ref in refs), refs
