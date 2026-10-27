# security-issues — tasks

- [x] 1. `scripts/security_issues.py` — plan / apply / check, one issue per (advisory, package)
- [x] 2. Selection from `data/security-policy.json` (`issue_severities` + `require_fix`), never a literal in the script
- [x] 3. The marker key (`<!-- security-finding: source:advisory:package -->`) plus `MARKER_RE` round-trip, asserted in the gate
- [x] 4. Label roster with colour + description, created on first use: security, vulnerability, severity:*, component:*, auto-fixable
- [x] 5. Structured body: advisory/scanner, package, current → fixed, severity, run link, suggested action, Not covered
- [x] 6. Idempotency: a second apply edits the same issue (no duplicate); a vanished advisory is closed with the clearing run and a refusal is a warning
- [x] 7. Make targets `security-issues`, `security-issues-plan`, `check-security-issues`; `.PHONY`, `check-security-issues` in `ci-unit`, classified in `scripts/issue_bot_gates.py`
- [x] 8. `security-scan.yml` runs `make security-issues` after the verdict on non-PR events (issues: write scoped to the job)
- [x] 9. `tests/test_security_issues.py` (9 tests, `gh` is a real recording stub) passing; `docs/SCANS.md` documents the targets; `check-docs` / `check-wiring` / `check-dispatch-forms` / `check-workflows` green
