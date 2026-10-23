# run-failure-reactor

## ADDED Requirements

### Requirement: Route B files an issue only for a failure that is still work

The reactor SHALL file a Route B issue only when the failure it routed is still actionable: a
`pull_request`-event run whose head still has an OPEN PR, or a `push` run that no later successful run of
the same workflow on the same branch has superseded. A failure whose subject is gone SHALL be reported as
`SUPERSEDED` and SHALL file nothing.

WHEN a completed failed run reaches Route B and its subject no longer exists
THEN no issue is filed, no label is applied, and the decision line names the reason.

#### Scenario: a merged PR's failed run files nothing

Given a failed `pull_request` run whose PR has merged and whose branch is gone
When  the reactor routes the run
Then  it prints `is SUPERSEDED` and creates no issue.

- **Test:** `tests/test_run_failure_reactor.py::test_a_merged_pr_run_files_nothing`

#### Scenario: a draft PR's failed run still files

Given a failed `pull_request` run whose PR is still OPEN but not pushable (a draft)
When  the reactor routes the run
Then  it still files exactly one issue, because that failure is live work.

- **Test:** `tests/test_run_failure_reactor.py::test_a_draft_fork_pr_run_files_an_issue_instead`
- **Test:** `tests/test_run_failure_reactor.py::test_a_later_failure_does_not_supersede_an_earlier_one`

#### Scenario: a main push superseded by a later green run files nothing

Given a failed `push` run on the default branch, and a later run of the same workflow on that branch that concluded `success`
When  the reactor routes the run
Then  it prints `is SUPERSEDED` and creates no issue.

- **Test:** `tests/test_run_failure_reactor.py::test_a_superseded_main_push_files_nothing`

#### Scenario: an un-superseded main push still files

Given a failed `push` run on the default branch with no later successful run on that branch
When  the reactor routes the run
Then  it files exactly one issue carrying the failing job, the log tail and the marker.

- **Test:** `tests/test_run_failure_reactor.py::test_a_red_main_run_with_no_pr_files_one_issue`

### Requirement: The superseded verdict is loud, never a silent skip

A decision not to file SHALL be printed as a greppable line naming the run and the reason. A crashed read
SHALL stay red: the reactor SHALL NOT treat "the API did not answer" as "the failure is superseded".

WHEN the reactor decides a failure is superseded
THEN the line `[run-fixer] run <id> is SUPERSEDED: <reason> - filing nothing` is printed and the exit code is 0.

#### Scenario: the reason is in the log

Given a superseded run
When  the reactor routes it
Then  stdout carries `is SUPERSEDED`, the run id and a reason naming what superseded it.

- **Test:** `tests/test_run_failure_reactor.py::test_a_superseded_main_push_files_nothing`

#### Scenario: an unreadable run list is not a superseded verdict

Given the run-list read fails
When  the reactor routes a `push` run
Then  the run is not declared superseded on the strength of a failed read.

- **Test:** `tests/test_run_failure_reactor.py::test_an_unreadable_run_list_is_not_a_supersede`

### Requirement: The dedupe marker stays sha-scoped

The marker SHALL keep naming the head sha, so routing the same run twice files nothing while a same-job
failure on a different head remains its own work item.

WHEN the same run is routed twice
THEN the second routing files nothing because the marker is already filed.

#### Scenario: the same head sha again files nothing

Given an OPEN issue already carrying the marker for this workflow/job@head-sha
When  the reactor routes the same run again
Then  it files nothing and exits 0.

- **Test:** `tests/test_run_failure_reactor.py::test_the_same_head_sha_again_files_nothing`
