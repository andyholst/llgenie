# No secret value reaches a log — for every key, not just the JEV one (#283)

## Why

`agent_jev_preflight.sh` got its own redaction and its own tests with #238/#282. Every OTHER key in
this repo relied on convention: a CI secret, `docker run -e VAR` (the name, never `VAR=value`), and a
guard that prints only the variable's name. That convention is one line away from breaking — an echo of
a token variable, a `set -x` in a script that reads a key, or `${{ secrets.X }}` interpolated into a
`run:` block instead of an `env:` — and nothing caught it.

GitHub masks a registered secret in its own logs, and that is not a guarantee: masking filters the log
stream, so a *transformed* value (base64, URL-encoded, sliced) passes through, and nothing at all is
masked in a log the job uploads itself. A value on a command line (`-e KEY=$KEY`) is public to every
process on the runner (`ps`), not just to the log.

## What was added

`scripts/check_secret_output.py` — `check` (the `ci-unit` gate) and `report` (which files name a
secret, and whether any of them prints it). Six rules, each with a name so a failure explains itself:

| rule | fails on |
|---|---|
| `secrets-in-run-block` | `${{ secrets.X }}` inside a `run:` block (it becomes script text and output) |
| `prints-secret-value` | a printing command that expands a secret's value |
| `xtrace-with-secrets` | `set -x` at a command position in a file that also reads a secret |
| `value-in-argv` | `-e VAR=$VAR` / `--build-arg VAR=$VAR` / `-e VAR=${{ … }}` |
| `env-dump` | a bare `env` / `printenv` reaching the log |
| `key-shaped-literal` | a committed credential-shaped literal |

Deliberate exemptions are visible, not silent: a file whose credentials are test values carries
`secret-output: test value`; the check's own source and its test are skipped by path (a check that
exempts the thing it checks is not a check), and nothing else is.

## Two false positives that shaped the rules (measured, not guessed)

1. **`key-shaped-literal` fired on 13 fixture names** (`hf_get_wrapped`, `hf_download_stall`,
   `jev-NEVER-PRINT-THIS-…`). A real token's body is a bare alphanumeric run, so the pattern now
   requires 20+ `[A-Za-z0-9]` after the prefix — and deliberate test values carry the marker.
2. **`xtrace-with-secrets` fired on the guard's own help line**, which *documents* `set -x`, and
   **`prints-secret-value`** fired on the help line that documented an echo of a token variable. The
   xtrace rule now requires a command position, and the help text contains neither spelling. A rule
   that fires on its own documentation gets muted, which is worse than no rule.

## Verified

- `make check-secret-output` → **OK, 217 files scanned**, no violation. `make secret-output-report` →
  35 files name a secret-shaped variable, **none** prints it.
- `tests/test_secret_output.py` — **19 tests**: every rule broken on a fixture file (with the rule id
  asserted), the exemptions (`-e VAR` alone, a redirect into `$HERMES_HOME/.env`, a
  `test -n "$KEY" || echo "$KEY unset"` guard, `os.environ` in Python, a fixture name), the repo
  passing its own guard, the report, and the exit code CI gates on.
- Wired into `ci-unit` and `test-unit`, `.PHONY`, `make help`, README.
