## ADDED Requirements

### Requirement: One issue per advisory and package, selected by policy

`make security-issues` MUST create exactly one issue per (advisory, package) pair, selected from the
reports by `issue_severities` in `data/security-policy.json`, and restricted to findings with a fixed
version when `require_fix` is true. A Medium finding MUST NOT become an issue while
`issue_severities` is critical+high.

#### Scenario: only the policy severities are filed

Given a report with CRITICAL, HIGH and MEDIUM findings,
When   the issues are selected,
Then   the CRITICAL and HIGH become issues and the MEDIUM does not.

- **Test:** `tests/test_security_issues.py::test_only_policy_severities_become_issues`

#### Scenario: an advisory without a fix is not filed

Given a CRITICAL advisory with no fixed version,
When   issues are selected with `require_fix: true`,
Then   nothing is filed, because nobody can act on it today.

- **Test:** `tests/test_security_issues.py::test_a_finding_without_a_fix_gets_no_issue`

### Requirement: The issue is tagged and self-describing

Every issue MUST carry `security`, `vulnerability`, one `severity:*`, one `component:*` and
`auto-fixable` when a fix exists, and its body MUST state the advisory (with scanner), the package,
current → fixed, the severity, the scan run, the suggested action and a `Not covered` section.

#### Scenario: the label set is complete per finding

Given a CRITICAL `numpy` finding and a HIGH `libssl` finding,
When   their issue labels are computed,
Then   the first is `component:python` and the second `component:container`, both carrying
       `security`, `vulnerability`, their severity and `auto-fixable`.

- **Test:** `tests/test_security_issues.py::test_labels_and_components_follow_the_finding`

#### Scenario: the body carries every required element

Given a finding and its run link,
When   the body is rendered,
Then   it contains the advisory id, the package, current and fixed versions, the link, the
       suggested action and `Not covered`.

- **Test:** `tests/test_security_issues.py::test_the_body_states_advisory_package_versions_and_action`

### Requirement: Filing is idempotent, and a cleared advisory is closed

The issue body MUST carry `<!-- security-finding: <source>:<advisory>:<package> -->`. Re-running
against the same finding MUST edit that issue and MUST NOT create a second one. An advisory present
in an open issue but absent from the reports MUST be closed with a comment naming the run that
cleared it; a closure `gh` refuses MUST NOT crash the run.

#### Scenario: a second run updates instead of duplicating

Given a tracker that already carries the finding's marker,
When   `make security-issues` runs,
Then   it issues an `issue edit` for that number and no `issue create`.

- **Test:** `tests/test_security_issues.py::test_apply_creates_then_updates_the_same_issue`

#### Scenario: a vanished advisory is closed

Given an open issue whose marker no longer appears in the reports,
When   `make security-issues` runs,
Then   that issue is closed with a comment naming the clearing run.

- **Test:** `tests/test_security_issues.py::test_a_vanished_finding_is_closed`

#### Scenario: the marker survives being written and read back

Given any (source, advisory, package),
When   the marker is rendered into a body and matched again,
Then   the same three parts come back.

- **Test:** `tests/test_security_issues.py::test_the_marker_round_trips`

### Requirement: The plan is readable without writing

`make security-issues-plan` MUST print what would be created or updated and MUST NOT touch GitHub.

#### Scenario: plan classifies and mutates nothing

Given two findings and one existing issue,
When   the plan is computed,
Then   it reports one create, one update and the keys to clear.

- **Test:** `tests/test_security_issues.py::test_plan_classifies_without_mutating`

### Requirement: The tracker configuration is gated

`make check-security-issues` (inside `make ci-unit`) MUST fail when `issue_severities` is empty or
not a subset of `fail_on`, when a required label is missing from the roster, or when the marker does
not round-trip.

#### Scenario: the shipped configuration is sane

Given this repository,
When   `make check-security-issues` runs,
Then   it exits 0 naming the label count, the severity set and the marker round-trip.

- **Test:** `tests/test_security_issues.py::test_the_real_policy_and_labels_are_sane`
