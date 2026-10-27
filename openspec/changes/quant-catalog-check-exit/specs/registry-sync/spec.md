# quant-catalog-check-exit

## ADDED Requirements

### Requirement: a check exits non-zero when it reports a finding

`scripts/gen_trending_quant_catalog.py --check` SHALL exit non-zero when the committed table differs from
the generated one or is missing, so `make check-quant-catalog` reds a stale table instead of printing a
diff nobody sees.

WHEN the committed catalog is stale
THEN the process exits non-zero.

#### Scenario: a stale catalog fails the check

Given a committed catalog that differs from what the generator produces
When  `make check-quant-catalog` runs
Then  it exits non-zero and the message names the file and `make sync-quant-catalog`.

- **Test:** `tests/test_script_exit_codes.py::test_every_main_that_returns_a_status_reaches_the_exit_code`
  (the static half: `main()` returns a value, so `__main__` must raise `SystemExit`); the behavioural half
  is the CI job `linux / unit` step `make ci-unit`, which runs `make check-quant-catalog`.

#### Scenario: a matching catalog passes the check

Given the committed catalog equals what the generator produces
When  `make check-quant-catalog` runs
Then  it exits zero and prints `OK`.

- **Test:** CI job `linux / unit` step `make ci-unit` (`make check-quant-catalog`), on the regenerated
  table committed with this change.

### Requirement: a `__main__` block never discards `main()`'s exit status

For every `scripts/*.py` whose `__main__` block calls `main()` without `sys.exit(...)` or
`raise SystemExit(...)`, `main()` SHALL NOT `return` a value. A script whose `main()` does return a status
must propagate it.

WHEN a script's `__main__` discards a non-`None` return from `main()`
THEN the guard test fails, naming the file and the line.

#### Scenario: the discarded status is caught before it ships

Given `scripts/gen_trending_quant_catalog.py` with `if __name__ == "__main__": main()` and a `main()` that
  returns 1
When  the guard runs
Then  it fails, naming that file and line.

- **Test:** `tests/test_script_exit_codes.py::test_every_main_that_returns_a_status_reaches_the_exit_code`

#### Scenario: a main() that returns nothing is not flagged

Given `scripts/llgenie_serve.py`, whose `main()` returns `None`
When  the guard runs
Then  it passes that file.

- **Test:** `tests/test_script_exit_codes.py::test_every_main_that_returns_a_status_reaches_the_exit_code`
