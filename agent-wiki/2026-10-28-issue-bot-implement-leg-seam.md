# issue-bot-implement-leg-seam — 2026-10-28

## What changed

- **`make agent-repo-ownership`** (new, `OWNERSHIP_DIR ?= $(CURDIR)`): runs `--entrypoint chown` in the
  pinned `$(AGENT_IMAGE)` to give the mounted checkout back to `$(id -u):$(id -g)`. `make implement-issue`
  calls it after the agent container returns, then `make issue-bot-pr-body-check`.
- **`scripts/issue_implementer.py`**: `body_problems(text)` is now the ONE four-part rule — `render_pr_body`
  (the `open-pr` path) and the new `check-body` subcommand both read it, so they cannot disagree. The
  subcommand fails naming the offending part, and fails loudly when `pr-body.md` does not exist.
- **`make issue-bot-pr-body-check`** (new): runs `check-body` with `BODY_FILE=`/`ISSUE=`, so the leg
  fails while the agent can still fix the body.
- **`.github/workflows/issue-bot.yml`**: the `Commit + push the feature branch` step runs
  `sudo chown -R "$(id -u):$(id -g)" .` **before** `git add -A` — the belt for a leg that ran an older
  image.
- **`tests/test_issue_bot_implement_leg.py`** (new): the pr-body rule through the real script (exit
  codes and messages), the recipe order, the chown shape, and the workflow step order.

## Why

Two measured runs died between "the work is done" and "the PR exists", each manufacturing a phantom
claim (`changed=true (make implement-issue rc=0)`, `PR: none opened`, a branch that 404s):

- **run 40673131217 (`ea80ab49`, #769)**: `git add -A` → `error: insufficient permission for adding an
  object to repository database .git/objects` → `fatal: updating files failed` → exit 128. The agent leg
  runs as **root** in a container over a writable mount, so `.git/objects` came back root-owned.
- **run 40591197166 (`b06f606d`, #759)**: the branch pushed, then the last step refused the PR —
  ``pr-body.md cannot become a PR body: `Technical:` states nothing`` — after every gate had passed.

The suspected causes (the commit-author allowlist, a missing `BUMP_TOKEN`) are **not** it: the identity
block ran clean in both logs.

## Decisions

- **Repair, don't re-run as non-root.** `--user $(id -u):$(id -g)` on the agent container would break the
  image's own setup (Hermes' HOME, the preflight); a chown pass inside the same pinned image needs no host
  privilege and fixes whatever the leg left, including objects written by tools inside it.
- **Both ends of the seam, not one.** The make target fixes the leg; the workflow's `sudo chown` fixes a
  checkout a leg from an older image already touched. A bot that only heals its next run leaves today's
  branch dead.
- **The body rule stays one function.** The pre-check exists so the failure happens early, not so the
  rule can drift: `check-body` and `open-pr` share `body_problems()`, and a test asserts they agree.
- **Fail closed on a missing body.** An absent `pr-body.md` is refused by name — a leg that wrote nothing
  cannot produce a PR, and a silent pass would recreate the phantom claim.

## Gates

- `tests/test_issue_bot_implement_leg.py` + `test_issue_implementer.py` + the workflow-hygiene files —
  130 passed.
- `make lint`, `check-wiring`, `check-docs`, `check-workflows`, `check-dispatch-forms`,
  `openspec-validate`, `openspec-tasks-check` — green.
- **The end-to-end proof is a real `issue-bot` run**: the ownership repair and the pr-body pre-check are
  only exercised when the bot implements an issue in CI, and this branch cannot demonstrate that from a
  laptop. The PR body says so instead of claiming a green nobody observed.

## Related

Issue [#770](https://github.com/asimov-agent/llgenie/issues/770) · #433 (root-owned artifacts from
container runs — the same class) · #759 / #769 (the two runs that died at this seam) · #427 (a run whose
implementation is missing stages nothing).
