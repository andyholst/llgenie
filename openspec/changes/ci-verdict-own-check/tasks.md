# Tasks

- [x] 1. `scripts/ci_verdict.py`: `own_check_run(jobs)` drops the judge's own `CHECK_NAME` row, wired into `jobs_of()` and into `main()` (the `--jobs` replay path too)
- [x] 2. `tests/test_ci_verdict.py`: `test_the_judges_own_check_run_is_not_counted_as_a_failure` (RED old / GREEN fix) and `test_a_real_unknown_failing_job_still_reds_even_with_the_fix` (the #1111 rule is not weakened)
- [x] 3. Guard-proven in the pinned `llgenie/test:latest` image: `test_ci_verdict.py` 22 passed / EXIT 0; `test_ci_scope.py` 43 passed / EXIT 0; stash RED on old code
- [x] 4. change-note trio: `docs/changes.d/2026-11-06-ci-verdict-own-check-1837.md` fragment, `agent-wiki` note, `CHANGES.md` row
