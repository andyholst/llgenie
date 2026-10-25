# fix-bot-sweep

## ADDED Requirements

### Requirement: The fix-bot's resolution answers "no PR" without failing

The fix-bot's `workflow_run` sweep SHALL resolve the failed run back to an open pull request, and SHALL
treat "no open pull request for this head" as an **answer**, not a failure: it SHALL exit 0, write an
empty `number=` to `$GITHUB_OUTPUT`, and say that there is nothing to repair. The merge gate SHALL keep
the opposite behaviour — nothing resolving SHALL fail loudly, naming the run and the head, and write no
value — so the lenient reading cannot reach the merge path. Both callers SHALL resolve through
`scripts/resolve_run_pr.py`, and the fix-bot SHALL reach it through `make fix-bot-resolve`.

WHEN a `CI` failure report arrives for a head whose pull request has already merged or closed
THEN the fix-bot sweep ends as a clean no-op instead of a red run,
AND  the merge gate keeps failing loudly when a run resolves to nothing.

#### Scenario: an already-landed PR ends the sweep cleanly

Given a finished `CI` run whose head branch has no open pull request
When  the fix-bot resolves that run with `--allow-none`
Then  it exits 0, writes the single line `number=` (empty), and says there is nothing to repair.

- **Test:** `tests/test_resolve_run_pr.py::test_allow_none_answers_no_pr_without_failing`

#### Scenario: the merge gate keeps its loud failure

Given the same finished run, resolved without `--allow-none`
When  nothing resolves
Then  the command exits 1 naming the run and the head, and writes no value at all.

- **Test:** `tests/test_resolve_run_pr.py::test_nothing_resolving_is_loud_and_writes_no_output`

#### Scenario: each workflow runs its own answer through make

Given the two workflows that resolve a run back to a PR
When  their resolution steps are read
Then  `fix-bot.yml` calls `make fix-bot-resolve` and `auto-merge.yml` calls `make auto-merge-resolve`,
AND  the lenient flag appears only in the fix-bot's make target.

- **Test:** `tests/test_resolve_run_pr.py::test_the_fix_bot_workflow_resolves_through_the_lenient_target`
- **Test:** `tests/test_resolve_run_pr.py::test_the_workflow_resolves_the_pr_through_the_make_target`
