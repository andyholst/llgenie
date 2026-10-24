# worktree-prune-retry

## ADDED Requirements

### Requirement: A branch held by a worktree is kept with its reason, never an error

When `git branch -D` refuses because a worktree holds the branch, and that worktree is not removable
debris (a branch is checked out there, or it holds uncommitted or unmerged work), the prune SHALL turn
that decision into a keep, print the reason naming the worktree, and continue — the run SHALL NOT exit
non-zero for it.

WHEN the branch delete is refused by a worktree the prune may not touch
THEN the branch is kept, the reason names the worktree, and the outcome carries no error.

#### Scenario: a dirty or branch-holding worktree keeps its branch

Given a merged branch whose delete is refused by a worktree that is not debris
When  the plan is applied
Then  nothing errors, the branch is kept, and the reason names the holding worktree.

- **Test:** `tests/test_worktree_prune.py::test_apply_turns_a_branch_held_by_a_worktree_into_a_keep`

#### Scenario: the real checkout exits zero

Given this checkout, whose `fix/rebase-behind-despite-comment` is held by a detached worktree with unmerged entries
When  `make worktree-prune` runs
Then  it prints a keep naming that worktree and exits 0.

- **Test:** `tests/test_worktree_prune.py::test_apply_turns_a_branch_held_by_a_worktree_into_a_keep`

### Requirement: Removable debris is removed, then the delete is retried once

A refusal naming a worktree that `worktree list --porcelain` reports as detached, branch-less and clean
SHALL cause the prune to remove that directory and retry the branch delete exactly once. A second
refusal SHALL remain an error naming the worktree.

WHEN the refusal names a clean, branch-less, detached worktree
THEN it is removed, the branch is deleted, and the retry happens once.

#### Scenario: the debris is removed and the retry deletes the branch

Given a refusal by a clean detached worktree with no branch line
When  the plan is applied
Then  the worktree is removed, the branch is deleted, and `branch -D` was called twice.

- **Test:** `tests/test_worktree_prune.py::test_apply_removes_a_clean_detached_holder_and_retries_once`

#### Scenario: only detached, branch-less, clean worktrees qualify

Given a named worktree, a clean detached worktree, and a dirty detached worktree
When  each is checked for removable debris
Then  only the clean detached one qualifies.

- **Test:** `tests/test_worktree_prune.py::test_the_refusal_helpers_read_gits_own_evidence`

### Requirement: An unattributable refusal stays an error

A `git branch -D` failure that names no worktree SHALL remain an error, and the branch SHALL NOT be
reported as pruned.

WHEN the refusal names no worktree
THEN the outcome carries the error and no branch is reported removed.

#### Scenario: a failure unrelated to a worktree is not silenced

Given a `branch -D` failure that names no worktree
When  the plan is applied
Then  it is an error and the branch is not in the removed list.

- **Test:** `tests/test_worktree_prune.py::test_apply_still_errors_when_a_refusal_names_no_worktree`
