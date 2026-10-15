# The rebase bot: keep every open PR on `main`, one PR per run (issue #246)

## Why

AGENTS.md's own rule is that a PR behind `main` cannot be merged, so a stale PR silently blocks
itself until a human rebases it. Only one narrow class was handled before (`engine-bump-rebase.yml`,
`chore/engine-bump-*`, clean merges only, "a conflict is left for a human"); every feature branch
was left behind, and this session produced several and hit the child-conflict class twice.

## What

- `scripts/rebase_bot_sweep.py`: the decision, in code rather than in a CI `if:` (issue #107
  forbids a job that can skip itself). One PR per run, oldest first, from the merge state
  (`BEHIND` = clean rebase, `DIRTY` = conflicts to resolve), with a stated reason for every
  pass-over. A PR whose marker comment for today already exists is left alone — that is the whole
  loop guard, and it needs no label — and a fork this bot cannot push to is skipped.
- `scripts/rebase_bot.sh`: the work. Rebase with `rerere` **off**; on a conflict, hand the stopped
  rebase to the agent (the prompt carries what each side means and the hard rules: preserve both
  sides, never weaken a test, keep the recipe TAB); continue with `GIT_EDITOR=true`; refuse to
  publish if conflict markers remain; then check the structure (`make -n ci-unit`, `make lint`,
  `make check-wiring`) and push **`--force-with-lease` to the PR's own head remote**. Never merges.
- `.github/workflows/rebase-bot.yml`: **every 6 hours** plus manual dispatch, one job that always
  runs, owner-guarded, the agent inside the agent image. It deliberately does NOT trigger on
  `push: main`.
- `tests/test_rebase_bot_sweep.py` (8 passed) drives both halves: the sweep through a fake `gh`
  that records argv, and the actor against a **real scratch repository** with a conflicting branch,
  a bare "fork" remote and a stub agent — so the rebase, the conflict hand-off, the gates and the
  push to the fork are exercised for real, not described.

## Coexisting with the other bots

Three bots touch branches, so the sweep refuses three things: a PR whose **checks are in flight**
(a rebase would cancel the run that is deciding it), a **merely-behind PR that is red** (the
fix-bot's, since a rebase does not fix a failing test — but a *conflicted* red PR IS taken, because
the rebase is what makes it fixable at all), and a fork it cannot push to. The implementer cannot
be raced: it pushes a new branch and only then opens the PR, so its PRs are fresh by construction.
If the fix-bot (plain fast-forward push) and this bot (`--force-with-lease`) ever overlap, the
second push is rejected loudly — nothing is clobbered in either direction.

## Measured

- 10 passed in the new suite; the actor test proves the resolved file keeps **both** sides and that
  the published branch is the rebased one.
- `make lint`, `make check-wiring`, `openspec-validate NAME=rebase-bot` green with the change;
  README documents the two new targets for issue #257's gate.
