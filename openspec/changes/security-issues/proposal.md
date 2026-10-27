# security-issues — proposal

Issue: [#716](https://github.com/asimov-agent/llgenie/issues/716)
Parent: [#713](https://github.com/asimov-agent/llgenie/issues/713)
Blocked by: [#715](https://github.com/asimov-agent/llgenie/issues/715) (the reports it reads)

## Why

A scan that only writes SARIF leaves the work invisible: nobody is assigned it, nothing survives in
the tracker, and the remediation bot (#717) has nothing to read. The reports exist (#715); what is
missing is the step that turns them into tracked, labelled, idempotent work items.

## What Changes

- **`scripts/security_issues.py`** — `plan` (what `DRY=1` prints), `apply` (through `gh`), `check`
  (the gate). One issue per **(advisory, package)**, selected by `issue_severities` +
  `require_fix` from `data/security-policy.json`, never one per scan run.
- **The marker is the key**: `<!-- security-finding: <source>:<advisory>:<package> -->` in the body,
  so a re-scan finds the issue without any local state and **updates** it rather than duplicating.
- **Labels**, created with colour + description on first use: `security`, `vulnerability`,
  `severity:critical` / `severity:high` / `severity:medium`, `component:python` /
  `component:container` / `component:code`, `auto-fixable` when a fix exists.
- **The body** carries advisory + scanner, package, current → fixed, severity, the run link, the
  suggested action and a `Not covered` section.
- **Clearing**: an advisory no longer reported is commented with the run that cleared it and
  closed; a refusal (a remediation PR still references it) is a warning, never a crashed run.
- **Wiring**: `security-scan.yml` runs `make security-issues` after the verdict on `push`,
  `schedule` and manual dispatch — never on a `pull_request`, whose findings belong to the PR.
  `make check-security-issues` joins `make ci-unit`.

## Not covered

- Applying the fix and opening the PR — #717.
- Folding several advisories of one package into one issue: each advisory is its own finding and
  its own issue, so a closure maps to exactly one advisory.
- A dashboard; the label set is the filter.
