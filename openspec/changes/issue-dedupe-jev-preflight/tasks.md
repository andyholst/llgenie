# issue-dedupe-jev-preflight — tasks

- [x] `.github/workflows/issue-dedupe.yml`: `TYPESAFE_API_KEY` on the `dedup` job env, with the measured run/job ids in the comment
- [x] `.github/workflows/registry-sync-review.yml`: the same key on the `review` job env (identical latent defect)
- [x] `tests/test_agent_shell_keys.py`: `GUARD_CALL` / `_guard_keys` / `_guarded_legs`, and the derived rule `test_every_workflow_that_calls_an_agent_leg_sets_the_keys_its_guard_requires` over every workflow × every guarded leg, reusing #364's `_step_sets_key` scope
- [x] `tests/test_agent_shell_keys.py`: planted-defect case `test_the_guard_scope_detector_catches_the_802_shape` (job-level key and step-level key both pass; sibling step does not)
- [x] prove the rule catches the bug: `git stash` the two workflow fixes → `1 failed, 10 passed` naming `issue-dedupe.yml:dedup` and `registry-sync-review.yml:review`; restore → `11 passed`
- [x] prove the guard's own two paths: `env -u TYPESAFE_API_KEY python3 scripts/require_env.py TYPESAFE_API_KEY` → exit 2 `FATAL`; with the key → exit 0 `OK`
- [x] `docs/BOTS.md`: the "#363" section states the other end of the guard (job must carry the key), with run `40702295009`
- [x] `agent-wiki/2026-10-28-issue-dedupe-jev-preflight.md` + the `CHANGES.md` index row
- [x] file the analysis finding (the remaining hand-kept #364 rosters) as its own issue: #908
- [x] `make openspec-validate NAME=issue-dedupe-jev-preflight` exits 0
- [x] host gates green in the worktree: `make lint`, `make check-workflows`, `make check-docs`, `make check-wiring`, `make check-dispatch-forms`, and the unit modules in `llgenie/test:latest`
