# issue-dedup-bot

## ADDED Requirements

### Requirement: A claimed issue is never a candidate and never a target

An issue carrying any agent label SHALL be excluded from the duplicate sweep as both candidate and target.
The protected set is `agent:implement`, `agent:ready`, `agent:refined`, `agent:closed`, `agent:duplicate`.

WHEN the sweep lists candidates or is about to close a copy
THEN an issue carrying any of those labels is not considered.

#### Scenario: the candidate list drops every claimed issue

Given open issues where one carries `agent:implement`
When  the sweep lists candidates
Then  that issue is absent and the unclaimed ones remain.

- **Test:** `tests/test_issue_dedup.py::test_candidates_drop_every_claimed_issue`

#### Scenario: the copy is re-checked before it is closed

Given a copy that carries an agent label by the time the verdict lands
When  a duplicate verdict is applied to it
Then  nothing is closed.

- **Test:** `tests/test_issue_dedup.py::test_the_copy_is_never_touched_when_it_carries_an_agent_label`

### Requirement: The pair is deterministic and the older issue is canonical

The sweep SHALL pair open unclaimed issues by title+body token Jaccard (threshold 0.30) and SHALL treat the
older issue as the canonical one, writing both bodies and the required answer shape to `dedup-in.md`.

#### Scenario: the similar pair is chosen and the older one is canonical

Given two similar unclaimed issues and one unrelated issue
When  the best pair is computed
Then  the similar pair is chosen with the OLDER issue as the canonical one.

- **Test:** `tests/test_issue_dedup.py::test_the_most_similar_pair_is_chosen_with_the_older_one_canonical`
- **Test:** `tests/test_issue_dedup.py::test_pick_writes_the_pair_for_the_agent_leg`

### Requirement: A duplicate close retires the copy with evidence and queues the canonical

A duplicate verdict SHALL post exactly one comment on the copy citing the canonical issue and the evidence,
add `agent:duplicate`, close the copy, and queue the canonical with `agent:implement` when it carries no queue
label. A duplicate verdict without an `EVIDENCE:` block SHALL be refused.

WHEN the agent answers `DUPLICATE: #<older>` with evidence
THEN the copy is commented, labelled and closed, and the canonical is queued.

#### Scenario: the copy is retired and the canonical queued

Given an unclaimed copy whose canonical carries no queue label
When  a duplicate verdict with evidence is applied
Then  the copy is commented with a reference to the canonical, labelled `agent:duplicate`, closed, and the
canonical receives `agent:implement`.

- **Test:** `tests/test_issue_dedup.py::test_a_duplicate_close_retires_the_copy_and_queues_the_canonical`

#### Scenario: no evidence, no close

Given a duplicate verdict with no `EVIDENCE:` block
When  it is applied
Then  the run exits non-zero and mutates nothing.

- **Test:** `tests/test_issue_dedup.py::test_a_duplicate_close_without_evidence_is_refused`

#### Scenario: a distinct verdict changes nothing

Given a `DISTINCT:` verdict with a reason
When  it is applied
Then  neither issue is edited or closed.

- **Test:** `tests/test_issue_dedup.py::test_a_distinct_verdict_leaves_both_issues_open`

### Requirement: The sweep runs four times a day behind the shared guard

`issue-dedupe.yml` SHALL run on `cron: "37 */6 * * *"` and by `workflow_dispatch` behind the byte-identical
owner/collaborator guard, deciding at most one pair per run, and SHALL be described in the README dispatch
table.

#### Scenario: the workflow runs the three steps for one pair

Given `.github/workflows/issue-dedupe.yml`
When  its schedule and steps are read
Then  it declares the 4x/day cron, carries the byte-identical guard, and runs pick -> decide -> apply for the
one pair the pick chose.

- **Test:** `tests/test_dispatch_forms.py::test_this_repository_states_what_every_dispatchable_run_does`
- **Test:** `tests/test_workflow_guards.py::test_every_dispatchable_workflow_has_the_guard`
