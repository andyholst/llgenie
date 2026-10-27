# 2026-10-27 — a finding becomes exactly one tagged issue, and never a duplicate

Issue #716 (parent #713, blocked by #715). Branch `feat/security-issues`, cut from
`feat/security-scan-workflow` because it reads the reports that change writes.

## What was verified

- `make check-security-issues` → `OK: 9 labels, issue_severities=['critical','high'], marker
  round-trips`.
- `tests/test_security_issues.py` → 9 passed. The `gh` calls are asserted through a **real
  executable stub** on PATH that records its argv (`tests/fixtures`-style inline stub), so the
  product code that decides labels, markers and the create/update/clear split runs for real —
  only the external system is stood in for.
- `make check-docs` (222 targets documented), `check-wiring` (242 targets, CI reaches 94),
  `check-dispatch-forms`, `check-workflows` green.

## Decisions

- **One issue per (advisory, package).** Not one per run, not one per package: a closure then maps
  to exactly one advisory, which is what makes the tracker evidence about the code.
- **The marker is the key**, not a label or a title search: `<!-- security-finding:
  source:advisory:package -->` survives an edited title and needs no local state.
- **Selection is policy, not a literal**: `issue_severities` + `require_fix` from
  `data/security-policy.json`, gated to be a subset of `fail_on` — a finding the pipeline would not
  fail on must not quietly become a filed issue either.
- **`component:*` is derived, not guessed per rule**: SAST findings are `component:code`, a package
  whose name marks a container library is `component:container`, everything else the Python
  scanners report is `component:python`. The `Not covered` in the issue body says a transitive
  dependency is its own finding.
- **Issues are filed on non-PR events only.** A `pull_request` run's findings belong to that PR;
  filing them would open tracker noise for code that may never merge.
- **A closure `gh` refuses is a warning.** The remediation PR (#717) may legitimately still
  reference the issue; a crashed scan run would hide every other finding.
- **Labels are created with colour + description on first use**, so the roster in `LABELS` is the
  single source of truth and `check-security-issues` can gate it.

## Status

Implementation complete on the branch; the PR opens once #715 (and #714 before it) merge.
