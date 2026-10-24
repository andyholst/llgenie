# worktree-prune

## ADDED Requirements

### Requirement: A detached worktree parked on a merged branch's tip is that branch's checkout

The prune SHALL match a worktree git reports as detached to a branch whose tip equals the worktree's
HEAD, when exactly one such worktree exists, and SHALL then remove the worktree BEFORE deleting the
branch. A detached worktree parked on any other commit SHALL be left untouched.

WHEN a prunable branch has no named worktree but one detached worktree sits on its tip
THEN that worktree is removed first and the branch is deleted in the same run.

#### Scenario: the merged tip's detached worktree and its branch both go in one run

Given a squash-merged branch whose worktree is detached at the branch tip
When  the prune runs once
Then  both the worktree and the branch are gone and the summary reports one of each.

- **Test:** `tests/test_worktree_prune.py::test_a_detached_worktree_on_the_merged_tip_is_removed_with_its_branch`
- **Test:** `tests/test_worktree_prune.py::test_a_detached_worktree_of_a_merged_branch_is_pruned_in_one_run`

#### Scenario: a detached worktree on another commit is never removed

Given a detached worktree at an unrelated commit and a merged branch with no worktree
When  the prune runs
Then  the unrelated worktree survives and the branch is still pruned.

- **Test:** `tests/test_worktree_prune.py::test_a_detached_worktree_on_another_commit_is_never_removed`

### Requirement: The plan never promises zero worktrees for a branch that has one

The printed plan and the applied outcome SHALL describe the same decisions: a branch that will have its
worktree removed SHALL be counted as one worktree.

WHEN the plan is printed
THEN every prunable branch with a matched worktree contributes one to the worktree count.

#### Scenario: two merged branches with worktrees are both pruned in one run

Given two squash-merged branches, each with a clean worktree
When  the prune runs once
Then  both worktrees and both branches are gone and the summary says two of each.

- **Test:** `tests/test_worktree_prune.py::test_one_run_prunes_every_merged_branch_and_its_worktree`
