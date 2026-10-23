# run-failure-reactor

## ADDED Requirements

### Requirement: A failed run on a pushable fork PR is routed to the fix-bot

When a failed run reports no PR in its REST `pull_requests` array, the reactor SHALL resolve the PR from
the run's `head_branch` and `head_repository.owner.login` and SHALL route it to the fix-bot when its head
belongs to this repository or to the trusted fork (`andyholst`), using `fix_bot_sweep`'s eligibility rules
with `own_fork=` rather than its own copy. A fifth-party fork SHALL NOT be dispatched, and a dispatch SHALL
carry the owner identity from the environment (`DISPATCH_TOKEN`) — never argv — failing loudly when that
credential is missing.

WHEN a completed CI run has failed
THEN a PR this bot can push is claimed and dispatched to the fix-bot,
AND  everything else falls back to one deduped `agent:implement` issue as before.

#### Scenario: a red fork-PR run dispatches the fix-bot as the owner

Given a failed fork `pull_request` run whose REST `pull_requests` array is empty and whose head resolves
to an open, red, non-draft PR in the trusted fork
When  the reactor routes the run
Then  it claims that PR and dispatches the fix-bot for it with the owner token, and files no issue.

- **Test:** `tests/test_run_failure_reactor.py::test_a_red_fork_pr_run_dispatches_the_fix_bot_as_the_owner`

#### Scenario: a missing dispatch token is loud

Given the same fork PR but no `DISPATCH_TOKEN` in the environment
When  the reactor routes the run
Then  it exits non-zero naming the variable, and neither dispatches the fix-bot nor files an issue.

- **Test:** `tests/test_run_failure_reactor.py::test_a_missing_dispatch_token_is_loud_and_dispatches_nothing`

#### Scenario: a fifth-party fork is not dispatched

Given a failed run whose head lives in a fork this repository does not own
When  the reactor routes the run
Then  it does not dispatch, says so, and falls back to the deduped issue.

- **Test:** `tests/test_run_failure_reactor.py::test_a_fifth_party_fork_run_is_not_dispatched`

#### Scenario: a draft fork PR still files an issue

Given a failed fork run whose PR is a draft
When  the reactor routes the run
Then  the fix-bot's own eligibility rule refuses it and the issue path runs instead.

- **Test:** `tests/test_run_failure_reactor.py::test_a_draft_fork_pr_run_files_an_issue_instead`

#### Scenario: a same-repo PR is still routed

Given a failed run whose REST `pull_requests` names an open same-repo PR
When  the reactor routes the run
Then  it claims and dispatches it exactly as before.

- **Test:** `tests/test_run_failure_reactor.py::test_a_red_same_repo_pr_run_dispatches_the_fix_bot`
