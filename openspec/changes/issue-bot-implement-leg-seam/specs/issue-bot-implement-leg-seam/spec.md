# issue-bot-implement-leg-seam

## ADDED Requirements

### Requirement: a root-run agent leg must not leave the checkout unwritable
After the containerized agent step returns, the implement leg MUST give the mounted checkout back to
the user that invoked it, so the step that stages and commits can write `.git/objects`.

WHEN `make implement-issue` returns from the agent container
THEN `make agent-repo-ownership` has chowned the mount to `$(id -u):$(id -g)` inside the pinned agent
image
AND the workflow's commit step repairs the same ownership before `git add -A`, as the belt for a leg
that ran an older image.

#### Scenario: the runner can stage after a root-owned container leg
- **Given** a checkout a container ran as root in, with root-owned `.git/objects`
- **When** the implement leg reaches its commit step
- **Then** the ownership repair has run before `git add -A`
- **And** `git add` cannot fail with `insufficient permission for adding an object to repository database`
- **Test:** `tests/test_issue_bot_implement_leg.py::test_the_push_step_repairs_ownership_before_it_stages_anything`

#### Scenario: the repair is part of the leg, not only of the workflow
- **Given** `make implement-issue`
- **When** its recipe runs
- **Then** it calls `agent-repo-ownership` after the container line, before the pr-body check
- **Test:** `tests/test_issue_bot_implement_leg.py::test_the_implement_recipe_repairs_ownership_and_checks_the_body_before_returning`

### Requirement: a PR body that cannot become a PR fails where the leg can still act
The leg MUST validate the agent's `pr-body.md` (all four parts present and non-empty, the issue named)
inside `implement-issue`, and MUST fail naming the offending part rather than at the final PR step.

WHEN the agent's `pr-body.md` has an empty or missing `Issue:`/`Fix:`/`Benefit:`/`Technical:` part
THEN `make issue-bot-pr-body-check` exits non-zero naming that part
AND a complete body passes.

#### Scenario: the #759 shape — `Technical:` states nothing
- **Given** a body whose `Technical:` line carries nothing
- **When** the check runs
- **Then** it exits 1 and the message names `Technical:` and says it states nothing
- **Test:** `tests/test_issue_bot_implement_leg.py::test_a_body_with_an_empty_technical_part_is_refused_by_name`

#### Scenario: no body at all is a loud failure
- **Given** no `pr-body.md`
- **When** the check runs
- **Then** it exits 1 saying the leg must write it
- **Test:** `tests/test_issue_bot_implement_leg.py::test_a_complete_body_passes_and_a_missing_file_is_loud`

### Requirement: one rule for the PR body, two callers
The four-part validation MUST be one function used by both the leg's pre-check and the `open-pr` path,
so the two can never disagree.

WHEN either caller reads a body
THEN both report the same problems for the same text.

#### Scenario: the helper and the renderer agree
- **Given** a body with an empty `Benefit:`
- **When** `body_problems()` and `render_pr_body()` read it
- **Then** both name `` `Benefit:` states nothing ``
- **Test:** `tests/test_issue_bot_implement_leg.py::test_body_problems_is_the_one_rule_both_paths_share`
