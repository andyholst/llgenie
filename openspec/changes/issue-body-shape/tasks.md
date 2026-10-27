# issue-body-shape — tasks

- [x] 1. `scripts/issue_body.py` — `render()` / `missing()` / `PRODUCERS`, six sections in order (`Acceptance criteria` tickable), `Technical` last, marker first line
- [x] 2. AGENTS.md — the new MANDATORY section, with the PR-body mapping and the producer roster
- [x] 3. `security_issues.body_for` renders through the seam (marker unchanged, `#716`'s dedupe intact)
- [x] 4. `code_review.issue_body`, `run_failure_reactor.issue_body`, `engine_skill_gap.issue_body` render through the seam
- [x] 5. `registry_change_issue.render`, `architecture_bot.render_issue`, `queued_run_alarm.file_label_issue` render through the seam
- [x] 6. `scripts/check_issue_body.py` + `make check-issue-bodies` / `make issue-bodies-report` (incl. the acceptance-criteria check), `.PHONY`, `##` help lines, documented in `docs/BOTS.md`
- [x] 7. `check-issue-bodies` in `make ci-unit`, classified in `scripts/issue_bot_gates.py` (deferred: `FAST_GATES` is #475's fixed list)
- [x] 8. `issue-triage` and `issue-refiner` skills state the six sections in their `REFINED:` / `RESTATED:` blocks
- [x] 9. Tests: `tests/test_issue_body.py`, `tests/test_check_issue_body.py`, and each producer's existing test asserting the rendered body
- [x] 10. Docs record: `docs/BOTS.md` contract paragraph, `agent-wiki/2026-10-27-issue-body-shape.md`, `CHANGES.md` row
- [x] 11. Verification: `make lint check-wiring check-docs check-agent-skills check-issue-bodies` green, `make test-unit` green, `make openspec-validate NAME=issue-body-shape` passes
- [x] 12. Follow-up `daf1e6b`: `_technical()` keeps a multi-line item a block, `queued_run_alarm.file_label_issue` passes its fenced report as that one item (no fence collision), and `tests/test_queued_run_alarm.py` asserts the filed body's headings from the recorded `issue create` argv
