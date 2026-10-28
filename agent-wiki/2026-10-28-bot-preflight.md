# 2026-10-28 — the bot preflight: prove the base, read the rulebook, cite it in the PR

Issue: [#792](https://github.com/asimov-agent/llgenie/issues/792) · PR:
[#856](https://github.com/asimov-agent/llgenie/pull/856) · OpenSpec change:
`openspec/changes/bot-preflight`

## What was measured

- `AGENTS.md` at `main@17cdcf3`: **87,255 bytes / 1,302 lines**. It is the referee for every leg, and
  four of its sections changed in the week ending 2026-10-28 (the commit-author allowlist, the
  issue-body shape #745, the agent-skill contract #577, the bot roster #349).
- The owner's checkout sat four commits behind `origin/main`; no bot flow computed
  `git rev-list --left-right --count HEAD...origin/main`, and neither a run log nor a PR said which
  `AGENTS.md` a leg had obeyed.
- `make bot-sync-main` (#303) already fetched and hard-reset. A reset answers "make it main"; it does
  not answer "is it main", and it records nothing.

## What the change does

- **`scripts/bot_preflight.py`** (stdlib only) + **`make bot-preflight`**: fetch `origin/main`,
  refuse a GitHub `origin` whose slug is not `asimov-agent/llgenie`, refuse a dirty tree,
  `git merge --ff-only` a behind tree, refuse a diverged one printing
  `git rev-list --left-right --count HEAD...origin/main`. Every refusal is exit **2**.
- **`preflight.txt`** (gitignored run input): `AGENTS: <main sha> <bytes>b <lines>l` first, then a
  `sha256` of the `## ` heading list, `MAIN`, `TREE`, `PROFILE`, `WHEN`. `CHECK=1` names the first
  field that disagrees with a reused file.
- **`make check-pr-hygiene`** rejects a body whose `AGENTS:` line is missing, whose sha is not an
  ancestor of both `HEAD` and the base (`git merge-base --is-ancestor`, never equality with the
  merge base — `rebase-bot` moves it), or whose counts are not `AGENTS.md` at that sha. The body comes
  from `--pr-body` / `--pr-body-file` / `$PR_BODY_FILE` / `$GITHUB_EVENT_PATH` — `gh` only when
  `PR=`+`REPO=` are passed. No body (a push to `main`) is a note, not a failure.
- **`bot-unattended`** states the preflight; `make check-agent-skills` fails when it is gone.
  `issue-implement` requires the line in `pr-body.md`.
- **Wired legs:** `issue-bot.yml` and `architecture-bot.yml` preflight right after `bot-sync-main`
  (sync = write, preflight = read that proves and records it); `fix-bot.yml` preflights after
  `bot-sync-branch`. `bot-sync-main` stays wired because an existing contract test pins it and the
  two answer different questions.

## Decisions

- **`--ff-only`, never a reset.** `bot-sync-main` stays the WRITE (new work resets to main,
  `bot-sync-branch` rebases a repair); the preflight is the READ that proves the result. A reset
  inside the preflight would have rewritten a tree it had just refused.
- **AHEAD passes.** The condition that matters is "nothing of `main` is missing"
  (`git merge-base --is-ancestor origin/main HEAD`), so a feature branch on top of main passes and a
  diverged branch is refused with the counts rather than silently rebased.
- **A local-path remote is accepted, a foreign GitHub remote is not.** Tests drive the real fetch,
  fast-forward and divergence through a bare repository on disk; the slug check only constrains
  GitHub URLs, so a mirror or a test remote is not mistaken for the upstream.
- **The heading digest, not a file digest.** A prose edit inside a section must not move it; adding
  or renaming a `## ` heading must. That is the difference between "the file changed" and "the rules
  changed".
- **The body source is resolved without network when one exists.** `ci-unit` already receives
  `GITHUB_EVENT_PATH`, and the implementer writes `pr-body.md` before the PR exists — those two cover
  CI and the pre-PR case, so `gh` is an explicit opt-in and the gate cannot go flaky on the network.
- **`AGENTS.md` does not yet carry a preflight section.** An agent run may not edit that file
  (protected: the write needs a human's approval), so the standing rule lives in `bot-unattended`
  and `docs/BOTS.md`, and the `AGENTS.md` section is filed as its own follow-up.
- **The cited sha must be a `main` the branch contains, not the merge base.** Comparing against
  `git merge-base origin/main HEAD` red every PR `rebase-bot` rebased, because the merge base moves
  whenever `main` does — measured on this very PR: the rebase moved `17cdcf3` → `0ddfda8` and the
  body's line would have been rejected. The gate now accepts a sha that is an ancestor of both the
  PR head and the base (the rulebook the leg really read is still reachable), and still checks the
  counts at that sha.
- **The counts come from the recorded sha, not the working tree.** `verify()` reads
  `AGENTS.md` with `git show <sha>:AGENTS.md`, so a branch that edits the rulebook writes a line its
  own `check-pr-hygiene` accepts (found as #865 while implementing this). Only an absent object
  falls back to the working tree, and the printed output names the source.
- **The `AGENTS:` rule is scoped to a bot range.** A PR is a bot PR when every commit it adds is
  authored by `Asimov Agent <support@docondee.com>` (`check_pr_hygiene.is_bot_pr`), **merge commits
  excluded** (`git log --no-merges`). Without that scope every PR a person opens would go red on
  `ci-unit` for a line stated nowhere they read — 7 of
  the 8 PRs open when this was written carry no `AGENTS:` line — and `auto-merge` would hold them
  all. The human identity is `andy.holst@protonmail.com` (`check_pr_authors.ALLOWED`); the bot's own
  implementer branch is all bot commits, so the check still fires where the contract applies.
- **The merge exclusion is what makes the rule fire in CI at all.** On a `pull_request` run
  `actions/checkout` hands the job `refs/pull/N/merge`, whose merge commit is authored by the merger;
  counting it made `is_bot_pr()` false on every bot PR, so the rule passed silently and nothing said
  so. Measured on this PR's own merge ref (`refs/pull/856/merge`, merge commit by
  `andy.holst@protonmail.com`): the previous code exits 0 on a body without the line, the fix exits 1
  naming the missing line; `undecidable_note()` now prints a NOTE when a range holds only merge
  commits. Pinned by
  `tests/test_pr_hygiene.py::test_a_non_bot_merge_commit_does_not_hide_a_bot_range`, which fails on
  the previous code.
- **The cited sha is an ancestor, not the merge base.** `git merge-base origin/main HEAD` moves
  every time `main` does, so a `rebase-bot` rebase invalidated a line whose `AGENTS.md` the leg
  really read and whose commit the branch still contains. The rule is now
  `git merge-base --is-ancestor <sha> <ref>` for both the head and the base; issue #792 AC3,
  `proposal.md`, the spec's `WHEN/THEN` and this note state that same rule.

## Status

Implementation and tests: `tests/test_bot_preflight.py` (real git pairs: at-main, ahead, behind →
fast-forwarded, dirty, diverged, foreign origin, unreachable remote, heading digest, stale `--check`,
gitignored record, Makefile/docs wiring), the `AGENTS:` cases in `tests/test_pr_hygiene.py`, and the
skill cases in `tests/test_agent_skills.py`.

Gates run on this branch (real output): `make check-pr-hygiene`,
`make check-agent-skills`, `make check-wiring`, `make check-workflows`, `make check-docs`,
`make lint`, `make openspec-validate NAME=bot-preflight` — all exit 0.
