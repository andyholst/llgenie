# bot-worktree-report — proposal

Issue: [#794](https://github.com/asimov-agent/llgenie/issues/794)

## Why

A host bot starts work with no idea what the bench looks like, and the one target that would clean it
up is destructive.

Measured 2026-10-28 on the owner's host, `/home/asimov/repository/git/llgenie` (main@17cdcf3):

- **37 worktrees** under `/home/asimov/repository/git/llgenie-wt/`, against `AGENTS.md:137`'s rule of
  *one agent, one worktree, one feature branch*.
- **7** whose branch tip is already an ancestor of `origin/main` and which has no open PR.
- **23** whose branch is not on `main` and which has no open PR — abandoned attempts.

Nothing in the flow reports that a previous run left a directory behind, and `AGENTS.md:483` tells the
agent to *"prune the branch **and** the worktree with `make worktree-prune`"* — a target that **deletes
directories**. That instruction is unsafe as written: the ancestry test cannot see uncommitted work,
and one of the "already merged" worktrees was `#759` mid-flight (branch tip an ancestor of `main`,
staged changes not committed). On 2026-10-28 a prune did exactly that to the #791 run: it deleted
`.worktrees/t_0af5476a` at 16:07Z with uncommitted work in it.

## What Changes

- **`scripts/worktree_report.py`** (new, stdlib only) — the measure-only preflight. It reads
  `git worktree list --porcelain`, and for each entry prints the path, the branch (or `detached`),
  `merged-into-main` (a real `git merge-base --is-ancestor <head> <base>`), `open-pr` (a real
  `gh pr list`) and `dirty` (a real `git status --porcelain` in that directory), then a summary line.
  It **mutates nothing**: no `git worktree remove`, no `git worktree prune`, no `git branch -D`.
  Exit 0 even when nothing is stale.
- **`scripts/worktree_prune_guard.py`** (new, stdlib only) — the seam `make worktree-prune` runs
  first. When the run is unattended and `CONFIRM=1` is absent, it refuses with a non-zero exit naming
  the marker that said "unattended", `make worktree-report` and the re-run spelling. "Unattended" is
  every lane a bot actually takes, because a marker a leg cannot receive is a gate that never fires
  (the first review's finding): `CI` (set by GitHub in every workflow step), `BOT` (forwarded by the
  Makefile's `AGENT_BOT_MARKER` as `-e BOT=1` on **every** agent-image `docker run`, since docker
  inherits no host environment and the image sets no such `ENV`), and the dispatcher's
  `HERMES_KANBAN_TASK` / `HERMES_KANBAN_WORKSPACE` / `HERMES_KANBAN_BRANCH` /
  `HERMES_KANBAN_WORKSPACES_ROOT` (a lane spawned on the host). For the owner (no marker set) it is a
  no-op, so the owner's cleanup path is unchanged.
- **`make worktree-report`** — new target, `##` help line, `.PHONY`, documented in `docs/BOTS.md`.
- **`make worktree-prune`** — same recipe, prefixed by the guard. No change to
  `scripts/worktree_prune.py`'s logic (issue #759 owns that half).
- **The bot contracts carry the prohibition**: `.hermes/skills/bot-unattended/SKILL.md` (preloaded by
  every leg) and `.hermes/skills/issue-implement/SKILL.md` (the leg that owns a host worktree). The
  `AGENTS.md:483` edit and the `agents/<profile>/SOUL.md` edits of criterion 5 are **OWED**, recorded
  in the PR body with their exact intended text rather than silently dropped: this session's write
  gate refuses edits to a protected agent-instruction file with no user present, and #791's
  `agents/` tree is still an open PR, so those paths do not exist yet.
- **`tests/test_worktree_report.py`** exercises a real temporary repository (real worktrees, a real
  squash-merged branch, a real dirty tree) with `gh` stubbed on `PATH` — the repository's documented
  allowance for an external CLI — and asserts `git worktree list` is byte-identical before and after
  the report.

## Not covered

- The root-owned-debris half of the prune (it unregisters a worktree but cannot delete the directory,
  exiting 2) — that is #759.
- Deleting the 37 existing worktrees: an owner action, not a bot's.
- The two `agents/<profile>/SOUL.md` edits (criterion 5): they need #791's `agents/` tree on `main`,
  so they are **filed as their own linked work item — [#876](https://github.com/asimov-agent/llgenie/issues/876)** —
  and named as OWED in the PR body; #876 in turn names #794 and PR #847.
