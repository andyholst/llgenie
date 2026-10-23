# A failed fork-PR run is repaired, not filed

Issue: #555. PR: (opened with this change).

The reactor's Route A never fired on this repository: it reads the REST run object's `pull_requests`,
which is empty for a fork `pull_request` run (#277/#170), and it refused a fork head outright — while every
agent PR lives in `andyholst/llgenie`. So every red agent-PR run became a new `agent:implement` issue
(#507, #537, #542 all carry `event: pull_request`), and the dispatched run, when one did happen, died in
fix-bot's own guard because `gh workflow run` carried the job token (`github-actions[bot]`, run
`39917926028`).

Route A now resolves the PR from the run's `head_branch` + `head_repository.owner.login` with
`scripts/resolve_run_pr.py`, passes it through `fix_bot_sweep.eligible(..., own_fork="andyholst")` (the
sweep's own rules, never a copy), and dispatches with `DISPATCH_TOKEN` from the environment — the owner
identity, never on argv. A missing token fails loudly; a fifth-party fork and a draft still fall back to
the deduped issue.

Verified: `pytest tests/test_run_failure_reactor.py` → 13 passed (5 new cases: fork dispatch + owner
token, missing token loud, fifth-party fork, draft fork, same-repo unchanged).
