## ADDED Requirements

### Requirement: Every scanner is invoked from its pinned image, in one place

`scripts/security_scan.py` MUST be the only code that invokes a scanner, and each invocation MUST
name the ref `containers/scanners/digests.json` records for that scanner. The workflow MUST call it
through `make` targets, never by inlining a scanner command.

#### Scenario: the workflow runs the make seam and never a bare scanner

Given `.github/workflows/security-scan.yml`,
When   its steps are read,
Then   it calls `make security-scan-all` and `make security-verdict`, and every `uses:` is a full
       40-hex commit SHA.

- **Test:** `tests/test_security_scan.py::test_the_workflow_uses_the_digests_and_a_manual_form`

#### Scenario: a scanner ref comes from the digests file

Given `containers/scanners/digests.json`,
When   the ref for a tool is asked for,
Then   it is `<registry>/llgenie/<tool>:<content hash>` from that file's recorded tag.

- **Test:** `tests/test_security_scan.py::test_the_policy_and_digests_are_sane` (plus
  `make scanner-ref TOOL=trivy`)

### Requirement: The pinned image is obtained, never skipped

The run MUST use the ref `containers/scanners/digests.json` names: pull it when published, and when
it cannot be pulled build the SAME `containers/scanners/<id>/Dockerfile` and tag it with that same
ref. A build failure MUST fail the run.

#### Scenario: an unpublished image is built, not skipped

Given a scanner ref that is not on the registry (a pull_request run before the first publish),
When   the image is resolved,
Then   the Dockerfile under `containers/scanners/<id>` is built, tagged with the requested ref, and
       the scan runs against it.

- **Test:** `tests/test_security_scan.py::test_an_unpublished_image_is_built_from_the_same_dockerfile`

#### Scenario: a published image is pulled and nothing is built

Given a scanner ref that is already on the registry,
When   the image is resolved,
Then   it is pulled, and no build runs.

- **Test:** `tests/test_security_scan.py::test_a_published_image_is_pulled_and_used`

#### Scenario: an unobtainable scanner fails the run

Given a ref that cannot be pulled and a Dockerfile that cannot be built,
When   the image is resolved,
Then   the run fails naming the scanner.

- **Test:** `tests/test_security_scan.py::test_a_failed_build_is_loud`

### Requirement: The failure policy is data, and a PR run is narrower than the daily run

`data/security-policy.json` MUST carry `fail_on`, `pr_fail_on`, `require_fix` and
`issue_severities`. A `full` verdict MUST fail on `fail_on`; a `pr` verdict MUST fail on
`pr_fail_on`, which MUST be a subset of `fail_on`. When `require_fix` is true, a finding without a
fixed version MUST NOT block.

#### Scenario: full mode fails on a high with a fix

Given a report with a HIGH advisory that has a fixed version,
When   `make security-verdict MODE=full` runs,
Then   it exits non-zero and prints the advisory, package, current → fixed and severity.

- **Test:** `tests/test_security_scan.py::test_full_mode_fails_on_a_high_with_a_fix`

#### Scenario: pr mode does not fail on a pre-existing high

Given the same HIGH advisory,
When   `make security-verdict MODE=pr` runs,
Then   it exits 0, because a pre-existing High must not red every pull request.

- **Test:** `tests/test_security_scan.py::test_pr_mode_only_fails_on_critical`

#### Scenario: an advisory with no fix never blocks

Given a CRITICAL advisory with no fixed version,
When   the policy requires a fix,
Then   it is recorded and the verdict does not fail.

- **Test:** `tests/test_security_scan.py::test_a_finding_without_a_fix_never_blocks`

#### Scenario: the policy and digests must agree

Given this repository,
When   `make check-security-scan` runs,
Then   it exits 0; an empty or unknown severity, `pr_fail_on ⊄ fail_on`, or a scanner missing from
       `digests.json` makes it exit non-zero.

- **Test:** `tests/test_security_scan.py::test_the_policy_and_digests_are_sane`

### Requirement: A scan that did not run is never a pass

A report that cannot be parsed MUST fail the run. A scanner that cannot run for lack of a token
MUST record the reason in its report and say so in the log; it MUST NOT be reported as clean.

#### Scenario: a corrupt report is a failure

Given a `trivy.json` that does not parse,
When   the findings are read,
Then   the run refuses with `does not parse` instead of answering zero findings.

- **Test:** `tests/test_security_scan.py::test_an_unparseable_report_is_not_a_pass`

### Requirement: The scan is manually dispatchable and gated

`.github/workflows/security-scan.yml` MUST trigger on `pull_request`, `push` to main, `schedule` and
`workflow_dispatch`, MUST declare its dispatch inputs with descriptions and defaults, and MUST run a
`guard` job — allowing the owner, `github-actions[bot]` on a same-repo head, and any collaborator
with `admin`/`maintain`/`write` — before any scanner runs.

#### Scenario: the manual form and the guard are present

Given the scan workflow,
When   `make check-dispatch-forms` runs,
Then   it passes: the workflow states what it does, every input is described with a default, and
       the `guard` job precedes the scan job.

- **Test:** `tests/test_security_scan.py::test_the_workflow_uses_the_digests_and_a_manual_form`
  plus `make check-dispatch-forms` (CI job `ci-unit`); the live dispatch is the workflow's own
  `workflow_dispatch` entry, visible at Actions → `security-scan`.
