# top-tier-timeout-retry — proposal

Issue: [#676](https://github.com/asimov-agent/llgenie/issues/676)

## Why

`tests/top_tier_dry_run.py::run_dry_run` is the bounded retry seam the `--dry` acceptance cases
shell out through (#399): a Hub transport failure is retried once, any other failure is returned at
once. But it called `subprocess.run(..., timeout=…)` **outside** any handler, so a child that
outlived its deadline raised `TimeoutExpired` straight out of the seam — no retry, and the caller
got a bare traceback instead of the CLI's named cause.

Measured twice on PR #661's `macos / top-tier` job (run 40332584088 then 40368450307), on changes
that never touch the dry run:

```
E  subprocess.TimeoutExpired: Command '… llgenie_serve.py --download-top-tier --family qwen
   --count 1 --dry' timed out after 780 seconds
FAILED tests/test_top_tier_acceptance.py::test_family_dry_run_known_lowend_one_provider
1 failed, 14 passed in 2278.52s (0:37:58)
```

The same case, in `llgenie/test:latest` on a developer host, passes in **237 s** — a third of that
budget. So the macOS runner is simply slower than the budget assumes, and the one mechanism built to
absorb a slow Hub moment never gets to run on a timeout.

## What Changes

- **`tests/top_tier_dry_run.py`** — `run_dry_run` catches `TimeoutExpired` and turns it into the same
  shape it already retries: a `CompletedProcess` with exit 124 and `timed out after <n> seconds` in
  its stderr (the existing `timed out` transient marker). It is retried within
  `TOP_TIER_DRY_RUN_ATTEMPTS`; if it times out on the last attempt the caller fails loudly **with
  the timeout named**, never with an escaping traceback and never a skip.
- **`.github/workflows/pipeline.yml`** — the `top-tier` job's `timeout-minutes` goes 60 → 90: the
  macOS stage alone measured 38 minutes, and the retry it is now guaranteed adds up to 780 s, which
  did not fit in the old ceiling with the job's setup.
- **`tests/test_top_tier_dry_run_retry.py`** — two cases over REAL child processes: a child that
  outlives a 1-second deadline is retried to the bound and then reported with the timeout named; a
  child that is slow only once is returned as a pass on the second attempt.

## Why not the alternatives

- **Bumping the timeout alone** does not fix the escaped exception: a slower runner still raises out
  of the seam, and the caller still sees a traceback rather than a named cause.
- **A `pytest.skip` on macOS** is forbidden by AGENTS.md, and the case genuinely runs there (it
  passed 14 of 15 siblings in the same job).
- **Dropping the case** would remove the only acceptance coverage of `--family` discovery.

## Not covered

- The runner's own provisioning or size: no schedule/runner change is proposed.
- Retry budgets for the other macOS stages; this change touches the dry-run seam and this job's
  ceiling only.
