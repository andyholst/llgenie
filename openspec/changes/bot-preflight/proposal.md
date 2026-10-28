# bot-preflight — proposal

Issue: [#792](https://github.com/asimov-agent/llgenie/issues/792)

## Why

A bot starts work from whatever tree it happens to be given, and nothing proves it read the rulebook
that was current when it started. Two measured facts on 2026-10-28:

- The owner's checkout sat four commits behind `origin/main` and nothing in any bot flow computed
  `git rev-list --left-right --count HEAD...origin/main`; only running it by hand showed the state.
- `AGENTS.md` is 87,255 bytes / 1,302 lines and is the referee for every leg. A leg that starts from
  a branch cut before a rule changed applies the old rule, and neither the run log nor the PR says
  which version of `AGENTS.md` it obeyed. This week alone changed the commit-author allowlist, the
  issue-body shape (#745), the agent-skill contract (#577) and the bot roster (#349).

`make bot-sync-main` (issue #303) already fetches and hard-resets — but it resets unconditionally,
so it hides the two states a leg must actually be told about: a **diverged** tree, and an
**unread** rulebook. It also records nothing, so no PR can be read against the rulebook.

## What Changes

- **`make bot-preflight`** → new `scripts/bot_preflight.py` (stdlib only). It fetches
  `origin/main`, refuses when `origin` is a GitHub remote other than `asimov-agent/llgenie`, refuses
  a dirty tree, fast-forwards a behind checkout (`git merge --ff-only`, never a rebase and never a
  reset), and refuses a **diverged** one by printing the left/right commit counts. Every refusal
  exits **2**; it never proceeds on a stale tree.
- **`preflight.txt`** (gitignored run input, like `issue.md`) records what the leg read:
  `AGENTS: <main sha> <bytes>b <lines>l` — the exact line a PR body carries — a `sha256` digest of
  the `## ` heading list (so a prose edit does not change it while a rule change does), the main
  sha, the tree's state and the profile. `--check` re-reads it against live values and prints the
  first difference, so a leg that reused a stale file is caught before it writes anything.
- **`make check-pr-hygiene`** gains the `AGENTS:` rule: a PR body must carry that line, its sha must
  be a `main` commit the PR contains — an **ancestor of both `HEAD` and the base**, not necessarily
  the merge base, because `rebase-bot` moves the merge base while the `AGENTS.md` the leg read stays
  reachable — and its counts must be those of `AGENTS.md` **at that sha**. A range is a bot range
  when every **non-merge** commit it adds is bot-authored (`--no-merges`, so the `refs/pull/N/merge`
  commit GitHub writes never makes a bot PR look human). The body is read without network:
  `--pr-body-file` / `$PR_BODY_FILE` (the implementer's `pr-body.md`, so a missing line is caught
  before the PR opens), `$GITHUB_EVENT_PATH`'s `pull_request.body` in `ci-unit`, or an explicit
  `PR=<n> REPO=<slug>` through `gh`.
- **`bot-unattended`** states the preflight as a rule every leg obeys, and `make check-agent-skills`
  fails when the shared skill loses it, so a leg cannot be written that omits it.
- The legs that already synced (`issue-bot`, `architecture-bot`) call the preflight instead, and the
  implementer's `issue-implement` skill requires the `AGENTS:` line in `pr-body.md`.

## Not covered

- Issue #845 — a worktree inherits the owner's current branch as its base; this change refuses the
  result, it does not change how the worktree is cut.
- Issue #794 — reporting the worktree a run is in.
- Issue #791 — the host agents' `agents/<profile>/SOUL.md` tree (not merged when this was written),
  so the standing rule is stated in `bot-unattended` + `docs/BOTS.md` here.
- `rebase-bot`'s staleness sweep (#246): that keeps an open PR current; this makes the start of
  work current. Neither replaces the other.
- The `## Bots preflight` section of `AGENTS.md` — the file is protected from agent writes (the edit
  needs a human approval an unattended run cannot obtain), so the standing rule lives in
  `bot-unattended` + `docs/BOTS.md` and the AGENTS.md section is filed as its own linked issue.
