# issue-bot-implement-leg-seam — proposal

Issue: [#770](https://github.com/asimov-agent/llgenie/issues/770)

## Why

The `issue-bot` implement leg dies between "the work is done" and "the PR exists", and the failure is
invisible in the one place a human looks: the leg reports `changed=true (make implement-issue rc=0)` and
`PR: none opened`, so the issue reads as implemented while its branch 404s. That is how #769's claim went
phantom and how #759's branch was pushed with no PR ever opened.

Two measured runs, two different causes — neither of them the suspected one (the commit-author allowlist
and `BUMP_TOKEN` are fine; the identity block ran):

- **run 40673131217, head `ea80ab49` (#769)** — `git add -A` dies with
  `error: insufficient permission for adding an object to repository database .git/objects`,
  `fatal: updating files failed`, exit 128. The agent leg runs in a container as **root**, so the
  objects it writes into the mounted checkout are root-owned and the runner's `git add` cannot insert
  into them.
- **run 40591197166, head `b06f606d` (#759)** — the branch pushed, then the **last** step refused the
  PR: `[issue-implementer] pr-body.md cannot become a PR body: `Technical:` states nothing` (exit 2).
  The gate was right; the leg had no way to notice until every gate had already run.

## What Changes

- `make agent-repo-ownership` gives the mounted checkout back to the invoking uid/gid, inside the pinned
  agent image (no host privileges needed). `make implement-issue` runs it after the agent container
  returns, so a root-run leg can never leave `.git` unwritable for the step that stages the work.
- `scripts/issue_implementer.py check-body` (+ `body_problems()`, now the one rule `render_pr_body` also
  uses) refuses a PR body whose `Issue:`/`Fix:`/`Benefit:`/`Technical:` part is missing or states
  nothing, naming the part. `make issue-bot-pr-body-check` runs it inside `implement-issue`, so the leg
  fails while it can still act instead of after the gate suite.
- `.github/workflows/issue-bot.yml`: the commit+push step repairs ownership before `git add -A`, the
  belt for a leg that ran an older image.

## Out of scope

- Why the scheduled slot fires hourly while the bot runs 3×/day, and the queue starvation that leaves
  PR checks pending (#817) — separate issues.
- `fix-bot` producing only `skipped` runs: by design of its gate, unrelated.
