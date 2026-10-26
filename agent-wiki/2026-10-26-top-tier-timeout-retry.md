# 2026-10-26 — a dry run that outlives its deadline is retried, not raised out of the seam

Issue: [#676](https://github.com/asimov-agent/llgenie/issues/676)
OpenSpec: `openspec/changes/top-tier-timeout-retry`
PR: (this branch)

## What was wrong

`tests/top_tier_dry_run.py::run_dry_run` is the bounded retry seam the `--dry` acceptance cases use
(#399). Its `subprocess.run(..., timeout=…)` sat **outside** any handler, so `TimeoutExpired` raised
straight through the seam — no retry, and the caller saw a traceback rather than the CLI's cause.

Measured twice on PR #661's `macos / top-tier` (run 40332584088, then 40368450307) on changes that
never touch the dry run:

```
subprocess.TimeoutExpired: Command '… --download-top-tier --family qwen --count 1 --dry'
  timed out after 780 seconds
FAILED tests/test_top_tier_acceptance.py::test_family_dry_run_known_lowend_one_provider
1 failed, 14 passed in 2278.52s (0:37:58)
```

The same case passes in 237 s in `llgenie/test:latest` on a developer host — the runner is simply
slower than a budget derived from a rate-limit cap (`RATE_LIMIT_WAIT_CAP + 180`).

## What changed

- `run_dry_run` catches `TimeoutExpired`, converts it to `CompletedProcess(returncode=124,
  stderr="… timed out after <n> seconds")` and treats it as the transient shape it already retries
  (`timed out` is in `TRANSIENT_MARKERS`). At the bound the caller fails with the timeout named.
- `pipeline.yml`: the `top-tier` job's `timeout-minutes` 60 → 90, so a retry fits above the 38-minute
  stage (setup included).
- `tests/test_top_tier_dry_run_retry.py`: two new cases over real child processes.

## Verified

- `tests/test_top_tier_dry_run_retry.py` — 10 passed (8 existing + 2 new) in `llgenie/test:latest`.
  The new cases use real `time.sleep` children and a 1–2 second deadline, so the timeout path is
  exercised, not mocked.
- The unchanged shapes are locked by the existing cases: a non-transient failure is still returned on
  the first attempt, and an always-transient child still spends the bound with a named cause.
