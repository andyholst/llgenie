# ci-verdict own-check-run exclusion (closes #1837)

2026-11-06 — the `ci-verdict` judge POSTs its verdict as a `ci-verdict` check-run on the judged run's head
(#1864). GitHub lists that posted row BACK as a job of the very run being judged (measured run 42275871131:
10 green jobs + an 11th `ci-verdict => failure`). `ci_scope.verify()` counted it as an unaccounted failure on
every re-judge — a self-referential permanent red blocking #1837.

Fix: `scripts/ci_verdict.py` gains `own_check_run()` which drops the judge's own `CHECK_NAME` row from the job
set before `verify()`, in both `jobs_of()` and the `--jobs` replay path. `verify()`'s rule that an unknown REAL
failing job is red stays intact. Guard-proven in the pinned image (GREEN 22 passed; stash RED 2 failed;
`test_ci_scope.py` 43 passed).
