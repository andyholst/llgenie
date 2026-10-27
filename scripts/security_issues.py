#!/usr/bin/env python3
"""Findings become TAGGED issues, idempotently (issue #716, parent #713).

A scan that only writes SARIF leaves the work invisible: nobody is assigned it, nothing survives in
the tracker, and the remediation bot (#717) has nothing to read. This module turns the reports
`make security-scan-all` writes into one issue per (advisory, package) — never one per scan run.

The lookup key is an HTML comment marker in the body, so the lookup needs no local state:

    <!-- security-finding: trivy:CVE-2024-1234:numpy -->

Re-running against the same reports **updates** that issue (last-seen, current → fixed, the run
link) and never opens a duplicate; a finding that is no longer reported is commented with the run
that cleared it and closed. Nothing is closed while a remediation PR is open (the bot comments on
it instead — #717 owns that half).

Commands (driven by make, never by hand):

    plan    print what would be created / updated / cleared, mutating nothing   make security-issues DRY=1
    apply   do it through `gh`                                                  make security-issues
    check   the label roster + the policy are sane                              make check-security-issues

`--repo` defaults to `$GITHUB_REPOSITORY`; `--reports` defaults to `security-reports`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import security_scan as ss  # noqa: E402

REPORTS = Path(os.environ.get("SECURITY_REPORTS") or (REPO / "security-reports"))
MARKER = "<!-- security-finding: {source}:{advisory}:{package} -->"
MARKER_RE = re.compile(r"<!--\s*security-finding:\s*([^:\s]+):([^:\s]+):([^>\s]+)\s*-->")
#: The labels every issue carries, and the colour/description each is created with.
LABELS: dict[str, tuple[str, str]] = {
    "security": ("b60205", "A vulnerability or a supply-chain finding"),
    "vulnerability": ("d93f0b", "An advisory with a known fix or a tracked exposure"),
    "severity:critical": ("b60205", "Scanner severity: critical"),
    "severity:high": ("e99695", "Scanner severity: high"),
    "severity:medium": ("fbca04", "Scanner severity: medium"),
    "component:python": ("1d76db", "A Python dependency (requirements*.in / tools/)"),
    "component:container": ("5319e7", "A container image or a Dockerfile base"),
    "component:code": ("0e8a16", "Application code (SAST finding)"),
    "auto-fixable": ("0e8a16", "The scanner names a fixed version the bot can apply"),
}


@dataclass
class Finding:
    """One advisory about one component, as the tracker sees it."""

    advisory: str
    package: str
    current: str
    fixed: str
    severity: str
    source: str
    component: str = ""
    labels: list[str] = field(default_factory=list)

    @property
    def marker(self) -> str:
        return MARKER.format(source=self.source, advisory=self.advisory, package=self.package)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.advisory}:{self.package}"

    @property
    def title(self) -> str:
        return f"security({self.severity}): {self.advisory} in {self.package} ({self.source})"


def component_of(package: str, source: str) -> str:
    """Which component a finding belongs to — the label a reviewer filters on.

    SAST findings are code by definition. A package named in the container images is a container
    one; anything else the Python scanners report is a Python dependency.
    """
    if source == "semgrep":
        return "component:code"
    container_markers = ("openssl", "libc", "wolfi", "debian", "ubuntu", "libssl", "zlib", "glibc")
    if any(marker in package.lower() for marker in container_markers):
        return "component:container"
    return "component:python"


def labels_for(severity: str, component: str, fixable: bool) -> list[str]:
    labels = ["security", "vulnerability", f"severity:{severity}", component]
    if fixable:
        labels.append("auto-fixable")
    return labels


def issue_findings(reports: Path = REPORTS, policy: dict | None = None) -> list[Finding]:
    """Every finding that must become an issue: severity in `issue_severities`, fix when required."""
    pol = policy or ss.policy()
    wanted = {str(s).lower() for s in pol.get("issue_severities") or ["critical", "high"]}
    out: list[Finding] = []
    seen: set[str] = set()
    for item in ss.findings(reports):
        if item["severity"] not in wanted:
            continue
        if pol.get("require_fix") and not item["fixed"]:
            continue
        advisory = item.get("id") or "unknown"
        package = item.get("package") or "unknown"
        finding = Finding(
            advisory=str(advisory), package=str(package), current=str(item.get("current") or ""),
            fixed=str(item.get("fixed") or ""), severity=item["severity"], source=item["source"],
        )
        finding.component = component_of(finding.package, finding.source)
        finding.labels = labels_for(finding.severity, finding.component, bool(finding.fixed))
        if finding.key in seen:  # one issue per (advisory, package), even across scanners
            continue
        seen.add(finding.key)
        out.append(finding)
    return sorted(out, key=lambda f: (f.severity, f.advisory, f.package))


def body_for(finding: Finding, run_url: str = "") -> str:
    return "\n".join([
        finding.marker,
        "",
        f"**Advisory:** `{finding.advisory}` — scanner: `{finding.source}`",
        f"**Affected package:** `{finding.package}`",
        f"**Current → fixed:** `{finding.current}` → `{finding.fixed}`",
        f"**Severity:** `{finding.severity}`",
        f"**Scan run:** {run_url or '(local `make security-scan-all`)'}",
        "",
        "### Suggested action",
        "",
        f"Bump `{finding.package}` from `{finding.current}` to `{finding.fixed}` (or drop the "
        "dependency), then let the pipeline re-scan. When the scanner no longer reports this "
        "advisory, the next scan comments the run that cleared it and closes this issue.",
        "",
        "### Not covered",
        "",
        "- Transitive dependencies this advisory pulls in are separate findings: each gets its own "
        "issue with its own advisory id.",
        "- A scanner that could not run (its report is absent) is not a clean result for this "
        "package: `make security-verdict` refuses instead of passing.",
    ])


def _gh(args: list[str], repo: str) -> subprocess.CompletedProcess:
    cmd = ["gh", *args, "--repo", repo]
    print(f"[security-issues] $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True)


def existing_issues(repo: str, label: str = "security") -> dict[str, dict]:
    """`{marker key: {number, body, labels}}` for every open security issue."""
    res = _gh(["issue", "list", "--label", label, "--state", "open", "--limit", "200",
               "--json", "number,body,labels,title"], repo)
    if res.returncode != 0:
        raise SystemExit(f"[security-issues] cannot list issues: {res.stderr.strip()}")
    out: dict[str, dict] = {}
    for issue in json.loads(res.stdout or "[]"):
        m = MARKER_RE.search(issue.get("body") or "")
        if m:
            out[f"{m.group(1)}:{m.group(2)}:{m.group(3)}"] = issue
    return out


def plan(findings: list[Finding], existing: dict[str, dict]) -> dict[str, list]:
    """What apply would do: create the new keys, update the known ones, clear the vanished ones."""
    keys = {f.key for f in findings}
    return {
        "create": [f for f in findings if f.key not in existing],
        "update": [f for f in findings if f.key in existing],
        "clear": [k for k in existing if k not in keys],
    }


def apply(findings: list[Finding], repo: str, run_url: str = "") -> int:
    existing = existing_issues(repo)
    actions = plan(findings, existing)
    for label, (colour, description) in LABELS.items():
        _gh(["label", "create", label, "--color", colour, "--description", description,
             "--force"], repo)
    for finding in actions["create"]:
        body = body_for(finding, run_url)
        args = ["issue", "create", "--title", finding.title, "--body", body]
        for label in finding.labels:
            args += ["--label", label]
        res = _gh(args, repo)
        if res.returncode != 0:
            raise SystemExit(f"[security-issues] create failed for {finding.key}: {res.stderr.strip()}")
        print(f"[security-issues] created: {finding.key} -> {res.stdout.strip()}")
    for finding in actions["update"]:
        issue = existing[finding.key]
        res = _gh(["issue", "edit", str(issue["number"]), "--body", body_for(finding, run_url)], repo)
        if res.returncode != 0:
            raise SystemExit(f"[security-issues] update failed for #{issue['number']}: {res.stderr.strip()}")
        print(f"[security-issues] updated: {finding.key} -> #{issue['number']}")
    for key in actions["clear"]:
        issue = existing[key]
        res = _gh(["issue", "close", str(issue["number"]), "--comment",
                   f"No longer reported by the latest scan ({run_url or 'local run'})."], repo)
        if res.returncode != 0:
            # A remediation PR may still reference it (#717); report, never crash the run.
            print(f"[security-issues] WARN: could not close #{issue['number']}: {res.stderr.strip()}")
    print(f"[security-issues] created={len(actions['create'])} updated={len(actions['update'])} "
          f"cleared={len(actions['clear'])}")
    return 0


def dry(findings: list[Finding]) -> int:
    """Print the plan and mutate nothing — the shape a reviewer reads before `apply` runs."""
    for finding in findings:
        print(f"CREATE {finding.title}")
        print(f"       labels: {', '.join(finding.labels)}")
        print(f"       marker: {finding.marker}")
        print(f"       {finding.current} -> {finding.fixed}")
    print(f"[security-issues] DRY: {len(findings)} issue(s) would be created or updated; nothing written")
    return 0


def check() -> int:
    """The label roster and the policy must be sane before an issue is filed."""
    problems: list[str] = []
    pol = ss.policy()
    severities = {str(s).lower() for s in pol.get("issue_severities") or []}
    if not severities:
        problems.append("security-policy.json: `issue_severities` is empty — no finding becomes an issue")
    if not severities <= {str(s).lower() for s in pol.get("fail_on") or []}:
        problems.append("security-policy.json: `issue_severities` is not a subset of `fail_on`")
    for severity in severities:
        if f"severity:{severity}" not in LABELS:
            problems.append(f"LABELS has no `severity:{severity}`: the issue cannot be filtered")
    for component in ("component:python", "component:container", "component:code"):
        if component not in LABELS:
            problems.append(f"LABELS has no `{component}`")
    if "auto-fixable" not in LABELS:
        problems.append("LABELS has no `auto-fixable`: the remediation bot has nothing to select")
    # The marker is the idempotency key: it must round-trip through MARKER_RE.
    for source, advisory, package in (("trivy", "CVE-1", "numpy"), ("semgrep", "rules.x", "a/b.py")):
        text = MARKER.format(source=source, advisory=advisory, package=package)
        m = MARKER_RE.search(text)
        if not m or (m.group(1), m.group(2), m.group(3)) != (source, advisory, package):
            problems.append(f"the marker does not round-trip for {source}:{advisory}:{package}")
    if problems:
        print(f"[security-issues] {len(problems)} problem(s):")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(f"[security-issues] OK: {len(LABELS)} labels, issue_severities={sorted(severities)}, "
          "marker round-trips")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("plan", "apply", "check"))
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--reports", default=str(REPORTS))
    ap.add_argument("--run-url", default=os.environ.get("SECURITY_RUN_URL", ""))
    args = ap.parse_args(argv)
    if args.command == "check":
        return check()
    findings = issue_findings(Path(args.reports))
    if args.command == "plan":
        return dry(findings)
    if not args.repo:
        raise SystemExit("[security-issues] set --repo (or $GITHUB_REPOSITORY) to file issues")
    return apply(findings, args.repo, args.run_url)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
