# security-scan-workflow — tasks

- [x] 1. `scripts/security_scan.py` — sbom / scan / all / verdict / check, every scanner invoked from the ref `containers/scanners/digests.json` names
- [x] 2. `data/security-policy.json` — fail_on, pr_fail_on, require_fix, issue_severities as data
- [x] 3. `require_fix` semantics: an advisory with no fixed version is recorded, never blocking; an unparseable report fails the run
- [x] 4. No scanner takes a secret: Trivy, Syft, Grype and Semgrep run from their pinned images, so no run is skipped for a missing token
- [x] 5. `.github/workflows/security-scan.yml` — pull_request / push / schedule / workflow_dispatch with a self-describing form, the guard job before any scanner, every `uses:` pinned to a commit SHA
- [x] 6. SARIF uploaded to the Security tab; CycloneDX SBOM + all reports uploaded as the `security-reports` artifact
- [x] 7. Make targets `sbom`, `security-scan`, `security-scan-all`, `security-verdict`, `check-security-scan`; `.PHONY`, `check-security-scan` in `ci-unit`, classified in `scripts/issue_bot_gates.py`
- [x] 8. `docs/BOTS.md` dispatch table regenerated; `make check-dispatch-forms` green
- [x] 9. `tests/test_security_scan.py` (9 tests) passing; `docs/SCANS.md` linked from `README.md`; `check-docs` / `check-wiring` / `check-workflows` green
