# top-tier-timeout-retry

## ADDED Requirements

### Requirement: a dry run that outlives its deadline is retried like any other transport failure

`tests/top_tier_dry_run.py::run_dry_run` MUST treat `subprocess.TimeoutExpired` as a transient
transport failure: the attempt is retried within `TOP_TIER_DRY_RUN_ATTEMPTS`, and when the bound is
spent the returned result MUST be a `CompletedProcess` whose non-zero exit and stderr NAME the
timeout (`timed out after <n> seconds`), so the caller fails loudly with a cause instead of an
escaping traceback. It MUST NOT skip the case and MUST NOT return a pass. A successful retry MUST be
returned as the result, exactly as for the other transient shapes. The `top-tier` job's
`timeout-minutes` MUST leave room for one full retry on top of the measured stage duration, so the
job ceiling never truncates the retry it promises.

WHEN a `--download-top-tier --dry` child is slower than its deadline
THEN the seam retries within its stated bound and, if the bound is spent, reports the timeout by name.

#### Scenario: a timeout that stays past the bound is named, not raised

- **Given** a child that always outlives a 1-second deadline
- **When** the real seam runs it
- **Then** it returns the stated number of attempts spent, a non-zero exit, and
  `timed out after 1 seconds` in stderr
- **Test:** `tests/test_top_tier_dry_run_retry.py::test_a_timeout_is_retried_and_then_named_at_the_bound`

#### Scenario: a timeout that clears on the retry passes

- **Given** a child that is slow only on its first run
- **When** the real seam runs it with a 2-second deadline
- **Then** the second attempt's zero exit is returned
- **Test:** `tests/test_top_tier_dry_run_retry.py::test_a_timeout_that_clears_on_the_retry_passes`
