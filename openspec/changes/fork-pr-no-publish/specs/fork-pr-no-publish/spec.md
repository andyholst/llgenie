# fork-pr-no-publish

## ADDED Requirements

### Requirement: a fork PR's refused publish is a loud skip, and only that refusal is forgiven

`scripts/engine_image.py::push` MUST skip the publish, exit 0, and announce it loudly when the
registry refuses a write with the permission denial (`denied: installation not allowed to Write
organization package`, or another spelling listed in `WRITE_DENIED`) **and** the run is a
`pull_request` (`GITHUB_EVENT_NAME=pull_request`). The announcement MUST be a `::warning::`
annotation naming the refused ref, the registry and issue #155, plus a `[engine-image] SKIP publish
<ref> …` log line. It MUST NOT be a `::notice`, MUST NOT use `continue-on-error`, and MUST NOT be
expressed as a scenario-scoped workflow `if:` — the decision lives in the script. Every other
outcome MUST stay a failure: the same denial on a push run, any other push failure (network, auth,
bad tag) on any run, and an image that fails its own version test before publishing. The tag step,
the pre-publish version test and the successful-publish output MUST be unchanged.

WHEN a fork PR moves an engine tag and its run publishes
THEN the build and post-build test still run, the refused publish is skipped with a warning naming
the ref and #155, and the job is green.

#### Scenario: the PR-#651 denial inside a pull_request run is a skip

- **Given** a `pull_request` run whose push is refused with `denied: installation not allowed to
  Write organization package`
- **When** the real `push()` runs
- **Then** it exits 0, prints the `::warning title=publish skipped::` annotation and a
  `SKIP publish` line naming issue #155, and prints no `FAIL push`
- **Test:** `tests/test_ci_publish_scope.py::test_a_fork_pr_skips_the_publish_it_cannot_be_granted`

#### Scenario: the same denial on a push run still fails

- **Given** a push run whose push is refused with the same message
- **When** the real `push()` runs
- **Then** it exits 1 and prints `FAIL push`, with no skip and no warning
- **Test:** `tests/test_ci_publish_scope.py::test_a_push_run_that_is_denied_still_fails`

#### Scenario: an unrelated pull_request failure is never forgiven

- **Given** a `pull_request` run whose push fails with `unauthorized: authentication required`
- **When** the real `push()` runs
- **Then** it exits 1 and prints `FAIL push`, because only the fork-write denial is a skip
- **Test:** `tests/test_ci_publish_scope.py::test_a_pull_request_denied_for_another_reason_still_fails`

#### Scenario: a successful publish is unchanged

- **Given** a run whose pushes are accepted
- **When** the real `push()` runs
- **Then** every publish ref is pushed and reported, with no skip and no warning
- **Test:** `tests/test_ci_publish_scope.py::test_a_successful_publish_is_unchanged`
