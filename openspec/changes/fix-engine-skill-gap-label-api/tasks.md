# Tasks

- [x] 1. `scripts/engine_skill_gap.py`: `_gh_api` + `_issue_labels` read/write the REST label endpoint (`repos/<repo>/issues/<n>/labels`), never `gh issue view`
- [x] 2. `scripts/engine_skill_gap.py`: `set_labels` POSTs the labels and reads them back, `SystemExit` naming the issue and the missing label when a label did not stick
- [x] 3. `scripts/engine_skill_gap.py`: `ensure_queue_label` repairs an existing tracking issue that lost `agent:implement` through the API
- [x] 4. `scripts/engine_skill_gap.py`: `open_issue` passes no `--label` on create and applies `bug` + `agent:implement` via `set_labels` (one POST + one read-back)
- [x] 5. `scripts/registry_change_issue.py`: `repo_slug`/`labels_of`/`set_labels`; `open_issue` creates without `--label`, aborts when the create URL carries no number, labels + reads back, and re-queues a marker issue that lost its label (the #710/#749 defect)
- [x] 6. `tests/test_engine_skill_gap.py`: the `gh` stand-in answers only the REST label endpoints and records every argv; spawn tests assert the POST, the read-back, no GraphQL write, and the loud failure
- [x] 7. `tests/test_registry_change_issue.py`: `_Gh` answers the REST label endpoints; create/update/dry-run/label-does-not-stick cases asserted with Given/When/Then markers
- [x] 8. Proved on the old tree: the new assertions fail on `HEAD`'s code (engine-skill-gap: 4 failed; registry-change-issue: 3 failed) and pass on this change (85 passed across both files)
- [x] 9. Live proof on the real tracker: issue #773 (`[]`) → `['agent:implement']` through `set_labels()`, read back by the product and by `gh api`
- [x] 10. `docs/BOTS.md` and `docs/ARCHITECTURE.md`: the claim that `gh issue edit --add-label` queues the tracking issue is replaced with the REST POST + read-back and the measured refusal
- [x] 11. `agent-wiki/2026-10-28-engine-skill-gap-label-api.md` records the work with the issue and the PR, and `CHANGES.md` indexes it
- [x] 12. Gates green: `make test-unit`, `make lint`, `make check-docs`, `make check-wiring`, `make openspec-validate NAME=fix-engine-skill-gap-label-api`
