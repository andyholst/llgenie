# security-daily-self-correct — proposal

Issue: [#738](https://github.com/asimov-agent/llgenie/issues/738)
Parent: [#713](https://github.com/asimov-agent/llgenie/issues/713)
Related: [#718](https://github.com/asimov-agent/llgenie/issues/718) — the Renovate config, which landed
separately (#722). This change adds no second `renovate.json` and no second schedule.
Deferred to: [#739](https://github.com/asimov-agent/llgenie/issues/739) (the agent leg for what the
floors and Renovate cannot place)

## Why

The scan gates the wrong runs and nothing closes what it reports. Measured on `main` (run
40525155122, a **push**): the job failed on 8 findings — `certifi`, `filelock`, `urllib3` — every one
a **transitive** pin in the generated `tools/requirements*.txt`. The remediation bot (#717) only
edits a *direct* pin in `tools/requirements*.in`, so it refuses all eight; there is no Renovate
config, so nothing bumps them on a schedule. The same advisory therefore reds the same job forever.

A scan belongs to its own daily pipeline. `main` CI answers "does this change work", never "is an
upstream package old today".

## What Changes

- **`.github/workflows/security-scan.yml` has no `pull_request:` and no `push:` trigger.** Its own
  daily `schedule` (04:05 UTC) and `workflow_dispatch` are the whole surface; the reports, the SARIF
  upload, the issues and the bump PR all live there. A `guard` job still refuses a stranger's
  dispatch.
- **Enforcement is data, scoped to an event.** `data/security-policy.json` gains
  `enforce_events: ["schedule", "workflow_dispatch"]`. `security_scan.verdict(event=…)` applies the
  full policy only for an event in that list and is report-only otherwise; `make
  check-security-scan` fails when the list is empty, names an unknown event, names `push` /
  `pull_request`, or when either of those triggers is re-added to the workflow.
- **The daily run self-corrects.** `scripts/security_bumps.py` derives, from the reports, the
  minimum version each advisory demands per package (the **maximum of the minimums** when several
  advisories name one package), writes them into `tools/security-floors.in`, regenerates
  `tools/requirements*.txt` through the ONE generator (`make -C tools generate-requirements*`), runs
  the fast gates, and opens or updates ONE PR that closes the tagged issues it fixes. A compiled
  `.txt` is never an edit target, and no version is invented: each floor is the scanner's own
  `fixed` value.
- **Gates and docs.** `make security-bumps-plan` / `security-bumps` (`DRY=1`) /
  `check-security-bumps` (inside `make ci-unit`); `tests/test_security_bumps.py`; `docs/SCANS.md`; an
  `agent-wiki/` note and its `CHANGES.md` row.

## Not covered

- The agent leg for what the floors and Renovate cannot place — #739.
- `make engine-bump` (the engines' own upstream pins) — an existing, different pipeline.
- Actions SHA pinning itself — #719.
- Renovate's own config and its low-risk automerge policy — #718, landed as #722.
