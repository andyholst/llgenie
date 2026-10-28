# Tasks — pr-matrix-trim-slow-rows (issue #859)

- [x] 1. OpenSpec change: `proposal.md`, `specs/ci-matrix-selection/spec.md`, this checklist
- [x] 2. `scripts/ci_slow_rows.py`: `decide(event, labels)` — PR without `ci:slow` → `["none"]` for `top-tier`, every other event → `["run"]` — with the `decide` CLI writing the `$GITHUB_OUTPUT` keys and one legible `[ci-slow-rows]` line
- [x] 3. `Makefile`: `ci-slow-rows` (`##` help, `.PHONY`) calling the script
- [x] 4. `ci.yml`: `guard` gains the checkout + decide step and the `top_tier_rows` output; the `linux` caller passes it and needs `guard`; header states the decision (and that the macOS half is #870's deletion)
- [x] 5. `pipeline.yml`: `top_tier_rows` input (default `["run"]`, fail closed); `top-tier` takes one `row` matrix axis, the placeholder runs no target and prints why, every working step gated on `matrix.row != 'none'`; `unit` / `cpu-health` untouched
- [x] 6. `docs/BOTS.md`: the trade in one paragraph — the row, the `ci:slow` label, the unchanged PR gates, the #870 deletion
- [x] 7. `tests/test_ci_slow_rows.py` (decision, label payload shapes, CLI outputs, run-log line, ci.yml wiring, the one matrix axis, the untouched gates, the documented trade) and the three tests that pinned the old step conditions / caller `with:` updated with their reason in place (`test_ci_images`, `test_macos_install`, `test_workflows_valid`)
- [x] 8. `agent-wiki/2026-10-28-pr-matrix-trim-slow-rows.md` + a `CHANGES.md` row
- [x] 9. Verified: `make check-workflows check-wiring check-docs check-issue-bodies check-dispatch-forms check-actions openspec-tasks-check lint`, `tests/test_ci_slow_rows.py` + `tests/test_ci_images.py` + `tests/test_macos_install.py` + `tests/test_workflows_valid.py` in `llgenie/test:latest`, `make test-unit` in `llgenie/test:latest`, `make openspec-validate NAME=pr-matrix-trim-slow-rows`; the negative control (the two workflows reverted, the new tests red) and the pushed PR's own run ids recorded in the PR body
