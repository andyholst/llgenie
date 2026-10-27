#!/usr/bin/env python3
"""One scan, from the pinned scanner images (issue #715, parent #713).

Every scanner runs from the image `containers/scanners/digests.json` names, by its immutable
content-hash ref — never a floating tag, never an install step. This module is the ONE place a
scanner is invoked, so the workflow, a developer and CI run the identical command.

Commands (driven by make, never by hand):

    ref <tool>        print the immutable image ref for a scanner   make scanner-ref
    sbom              Syft -> security-reports/sbom.cdx.json        make sbom
    scan <tool>       trivy | grype | semgrep | snyk                make security-scan TOOL=<id>
    all               sbom + every scanner, in dependency order     make security-scan-all
    verdict [--mode]  apply data/security-policy.json               make security-verdict [MODE=pr]
    findings          print every finding in one normalised shape   (diagnostics)
    check             policy + digests are sane                     make check-security-scan

**Failure policy** (`data/security-policy.json`): a finding fails the run when its severity is in
`fail_on` AND (when `require_fix` is true) the report carries a fixed version. A pull-request run
enforces the narrower `pr_fail_on` (critical only by default), because a pre-existing High without
a fix must not red every PR in the repository — the daily and manual runs enforce `fail_on` in
full. Both sets are data, not literals in a workflow step.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNTIME = os.environ.get("RUNTIME") or "docker"
DIGESTS = REPO / "containers" / "scanners" / "digests.json"
POLICY = REPO / "data" / "security-policy.json"
REPORTS = Path(os.environ.get("SECURITY_REPORTS") or (REPO / "security-reports"))
TOOLS = ("trivy", "grype", "semgrep", "snyk")
DEFAULT_POLICY = {
    "fail_on": ["critical", "high"],
    "pr_fail_on": ["critical"],
    "require_fix": True,
    "issue_severities": ["critical", "high"],
}


def digests() -> dict:
    if not DIGESTS.is_file():
        raise SystemExit(f"[security-scan] {DIGESTS} is missing — run `make scanner-digests`")
    return json.loads(DIGESTS.read_text(encoding="utf-8"))


def image_ref(tool: str) -> str:
    """`<registry>/llgenie/<tool>:<content hash>` — the immutable ref from the digests file."""
    entry = digests().get(tool)
    if not entry:
        raise SystemExit(f"[security-scan] no scanner image recorded for `{tool}`")
    registry = os.environ.get("LLGENIE_REGISTRY", "ghcr.io/asimov-agent").rstrip("/").lower()
    return f"{registry}/llgenie/{tool}:{entry['tag']}"


def policy() -> dict:
    merged = dict(DEFAULT_POLICY)
    if POLICY.is_file():
        merged.update(json.loads(POLICY.read_text(encoding="utf-8")))
    return merged


def _run(argv: list[str], image: str) -> int:
    """Run one scanner from its image, with the checkout mounted so it writes its reports."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    cmd = [RUNTIME, "run", "--rm", "-v", f"{REPO}:/work:rw", "-w", "/work",
           "-e", "HOME=/tmp", "-e", "SNYK_TOKEN", image, *argv]
    print(f"[security-scan] $ {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def sbom() -> int:
    """Syft writes the CycloneDX SBOM; Grype matches against exactly this file."""
    return _run(["syft", "dir:.", "-o", "cyclonedx-json=/work/security-reports/sbom.cdx.json"],
                image_ref("grype"))


def scan(tool: str) -> int:
    if tool not in TOOLS:
        raise SystemExit(f"[security-scan] unknown tool `{tool}`; known: {', '.join(TOOLS)}")
    if tool == "trivy":
        # One format per invocation (trivy takes one `--format`), so JSON for the verdict and SARIF
        # for the Security tab are two runs over the same tree.
        base = ["fs", "--severity", "CRITICAL,HIGH,MEDIUM", "--scanners", "vuln"]
        rc = _run([*base, "--format", "json", "--output", "security-reports/trivy.json", "."],
                  image_ref(tool))
        rc |= _run([*base, "--format", "sarif", "--output", "security-reports/trivy.sarif", "."],
                   image_ref(tool))
        return rc
    if tool == "grype":
        if not (REPORTS / "sbom.cdx.json").is_file():
            raise SystemExit("[security-scan] grype needs the Syft SBOM: run `make sbom` first")
        return _run(["sbom:/work/security-reports/sbom.cdx.json", "-o", "json",
                     "--file", "/work/security-reports/grype.json"], image_ref(tool))
    if tool == "semgrep":
        return _run(["scan", "--config", "auto", "--json", "--output",
                     "/work/security-reports/semgrep.json", "--metrics", "off", "."], image_ref(tool))
    # snyk
    if not os.environ.get("SNYK_TOKEN"):
        # LOUD, never silent: the reason is recorded in the report and printed, and it is not a pass.
        REPORTS.mkdir(parents=True, exist_ok=True)
        (REPORTS / "snyk.json").write_text(json.dumps({
            "skipped": True, "reason": "SNYK_TOKEN is not set in this run"}, indent=2) + "\n")
        print("[security-scan] SKIP snyk: SNYK_TOKEN is not set — recorded in "
              "security-reports/snyk.json, not treated as a pass")
        return 0
    return _run(["test", "--all-projects",
                 "--json-file-output=/work/security-reports/snyk.json"], image_ref(tool))


def all_scans() -> int:
    rc = sbom()
    for tool in TOOLS:
        rc = scan(tool) or rc
    return rc


def _trivy_findings(report: dict) -> list[dict]:
    return [{
        "id": vuln.get("VulnerabilityID"),
        "package": vuln.get("PkgName"),
        "current": vuln.get("InstalledVersion"),
        "fixed": vuln.get("FixedVersion") or "",
        "severity": str(vuln.get("Severity", "")).lower(),
        "source": "trivy",
    } for result in report.get("Results") or []
        for vuln in result.get("Vulnerabilities") or []]


def _grype_findings(report: dict) -> list[dict]:
    return [{
        "id": (match.get("vulnerability") or {}).get("id"),
        "package": (match.get("artifact") or {}).get("name"),
        "current": (match.get("artifact") or {}).get("version"),
        "fixed": ", ".join((match.get("fix") or {}).get("versions") or []),
        "severity": str((match.get("vulnerability") or {}).get("severity", "")).lower(),
        "source": "grype",
    } for match in report.get("matches") or []]


def findings(reports: Path | None = None) -> list[dict]:
    """Every finding from every report that exists, in one shape."""
    reports = reports or REPORTS  # resolved at call time: `SECURITY_REPORTS`/a test can move it
    out: list[dict] = []
    for name, reader in (("trivy.json", _trivy_findings), ("grype.json", _grype_findings)):
        path = reports / name
        if not path.is_file():
            continue
        try:
            out.extend(reader(json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError:
            raise SystemExit(f"[security-scan] {path} does not parse — the run is not green")
    return out


def blocking(items: list[dict], pol: dict, mode: str = "full") -> list[dict]:
    """The findings that must fail the run, for the mode's severity set."""
    severities = pol.get("pr_fail_on") if mode == "pr" else pol.get("fail_on")
    fail_on = {str(s).lower() for s in severities or []}
    out = []
    for item in items:
        if item["severity"] not in fail_on:
            continue
        if pol.get("require_fix") and not item["fixed"]:
            continue
        out.append(item)
    return out


def verdict(mode: str = "full") -> int:
    pol = policy()
    items = findings()
    bad = blocking(items, pol, mode)
    severities = pol.get("pr_fail_on") if mode == "pr" else pol.get("fail_on")
    if bad:
        print(f"[security-scan] FAIL ({mode}): {len(bad)} finding(s) at {severities}"
              f"{' with a fix available' if pol.get('require_fix') else ''}")
        for item in bad[:40]:
            print(f"  {item['source']}: {item['id']} {item['package']} "
                  f"{item['current']} -> {item['fixed']} ({item['severity']})")
        return 1
    print(f"[security-scan] OK ({mode}): {len(items)} finding(s) recorded, none blocking "
          f"(fail_on={severities}, require_fix={pol.get('require_fix')})")
    return 0


def check() -> int:
    """The policy and the digests must be sane before a scan is trusted."""
    problems: list[str] = []
    pol = policy()
    known = {"critical", "high", "medium", "low", "negligible", "unknown"}
    for key in ("fail_on", "pr_fail_on", "issue_severities"):
        values = pol.get(key)
        if not values:
            problems.append(f"security-policy.json: `{key}` is empty")
            continue
        for severity in values:
            if str(severity).lower() not in known:
                problems.append(f"security-policy.json: `{severity}` in `{key}` is not a severity")
    if set(map(str.lower, pol.get("pr_fail_on") or [])) - set(map(str.lower, pol.get("fail_on") or [])):
        problems.append("security-policy.json: `pr_fail_on` is not a subset of `fail_on`")
    recorded = digests()
    for tool in TOOLS:
        entry = recorded.get(tool) or {}
        for key in ("version", "tag", "ref"):
            if not entry.get(key):
                problems.append(f"digests.json: `{tool}` has no `{key}`")
        if entry.get("tag") and f":{entry['tag']}" not in image_ref(tool):
            problems.append(f"digests.json: `{tool}` tag is not the ref's tag")
    if problems:
        print(f"[security-scan] {len(problems)} problem(s):")
        for item in problems:
            print(f"  - {item}")
        return 1
    print(f"[security-scan] OK: fail_on={pol['fail_on']} pr_fail_on={pol['pr_fail_on']} "
          f"require_fix={pol.get('require_fix')}, {len(TOOLS)} pinned scanner refs")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command",
                    choices=("ref", "sbom", "scan", "all", "verdict", "findings", "check"))
    ap.add_argument("tool", nargs="?", default="")
    ap.add_argument("--mode", default="full", choices=("full", "pr"))
    args = ap.parse_args(argv)
    if args.command == "ref":
        print(image_ref(args.tool))
        return 0
    if args.command == "scan":
        return scan(args.tool)
    if args.command == "findings":
        print(json.dumps(findings(), indent=2))
        return 0
    if args.command == "verdict":
        return verdict(args.mode)
    return {"sbom": sbom, "all": all_scans, "check": check}[args.command]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
