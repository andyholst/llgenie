# security-scan-workflow — proposal

Issue: [#715](https://github.com/asimov-agent/llgenie/issues/715)
Parent: [#713](https://github.com/asimov-agent/llgenie/issues/713)
Blocked by: [#714](https://github.com/asimov-agent/llgenie/issues/714) (the scanner images land first)

## Why

The repository has no workflow that scans anything (`grep -rl 'trivy\|grype\|semgrep' .github`
→ empty) and no manual entry point for a scan. With #714 the scanner images exist; without a single
invocation seam, each caller would invent its own flags, its own severity threshold and its own idea
of what "green" means.

## What Changes

- **`scripts/security_scan.py`** — the one place a scanner is invoked: `sbom` (Syft → CycloneDX),
  `scan <tool>` (syft / trivy / grype / semgrep, each from the ref `containers/scanners/digests.json`
  names), `all`, `verdict [--mode full|pr]`, `check`. No scanner takes a secret, an unknown tool id
  is refused by name, and an unparseable report fails instead of reading as zero findings.
- **`data/security-policy.json`** — the policy as data: `fail_on` (critical+high), `pr_fail_on`
  (critical), `require_fix`, `issue_severities`. A pull-request run enforces the narrower set so a
  pre-existing High cannot red every PR; the daily and manual runs enforce the full set.
- **`.github/workflows/security-scan.yml`** — `pull_request`, `push` to main, daily `schedule`, and
  `workflow_dispatch` (`tools`, `enforce`) with the repository's `guard` job (owner / repository bot
  on a same-repo head / collaborator with write) running BEFORE any scanner. Every `uses:` is a full
  commit SHA. SARIF goes to the Security tab; the reports directory (CycloneDX SBOM included) is
  uploaded as an artifact.
- **Make targets** `sbom`, `security-scan`, `security-scan-all`, `security-verdict`,
  `check-security-scan`; the last is wired into `make ci-unit` (empty/unknown severities,
  `pr_fail_on ⊄ fail_on`, or a scanner missing from `digests.json` fails).
- **`docs/SCANS.md`** (linked from `README.md`) and `tests/test_security_scan.py`.

## Not covered

- Turning findings into tagged issues — #716 (it reads the reports this change writes).
- Applying fixes — #717.
- Container-image *scanning* of every published engine image (this scans the tree and the SBOM the
  tree produces); a per-image scan matrix is a separate decision.
