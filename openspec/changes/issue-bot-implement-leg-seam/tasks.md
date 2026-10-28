# issue-bot-implement-leg-seam — Tasks

Issue: [#770](https://github.com/asimov-agent/llgenie/issues/770)

- [x] 1. `make agent-repo-ownership` chowns the mounted checkout back to `$(id -u):$(id -g)` inside `$(AGENT_IMAGE)`; `OWNERSHIP_DIR` names the tree (default `$(CURDIR)`).
- [x] 2. `make implement-issue` runs `agent-repo-ownership`, then `issue-bot-pr-body-check`, after the agent container returns.
- [x] 3. `scripts/issue_implementer.py check-body` + `body_problems()` — the one rule `render_pr_body` also uses — refuses a missing/empty `Issue:`/`Fix:`/`Benefit:`/`Technical:` part and names it.
- [x] 4. `make issue-bot-pr-body-check` fails when `pr-body.md` is absent, and runs the check with `ISSUE=` so the body must name the issue.
- [x] 5. The `Commit + push the feature branch` step repairs ownership with `sudo chown -R "$(id -u):$(id -g)" .` **before** `git add -A`.
- [x] 6. `tests/test_issue_bot_implement_leg.py` locks the pr-body rule through the real script, the recipe order, the chown shape, and the workflow step order.
- [x] 7. `make lint`, `check-wiring`, `check-docs`, `check-workflows`, `check-dispatch-forms`, `openspec-validate`, `openspec-tasks-check` pass; the end-to-end proof is a real `issue-bot` run (recorded in the PR body, not claimed here).
