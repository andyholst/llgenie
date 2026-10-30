# Verifying an llgenie claim locally

Turning "the PR says" or "CI says" into an executed measurement at a named sha.

## Interpreter

Run the suite with the repo's own test venv (see `Makefile`: `VENV := $(HOME)/llama-gguf-tools/.venv`), not the tool-host python. `tests/conftest.py` imports `scripts.llgenie_serve`, whose re-exec shim reads `sys.argv[1:]`; flags like `-s` / `-x` are swallowed by that argparse and the run dies with exit 2 and **no output**. `-q`, `-k` and `-m` work. Shape that works:

```
<venv>/bin/python -m pytest tests/<file>.py -q -p no:cacheprovider
<venv>/bin/python -m pytest tests/<file>.py -k '<expr>' -m 'not network' -q
```

A bare exit 0 after a pipe is the pipe's status, not pytest's — never read `cmd | tail` as the verdict.

## Golden / fixture freshness

A fixture can appear in the PR's diff **and still be stale**: it was regenerated before a later commit in the same branch changed behaviour, so its rows describe an older product. The tell is that the red rows' values correspond to a deliberate change (a disabled build cell falling back, a reordered tier table), not to noise.

Prove staleness rather than assert it — regenerate with the repo's own target, re-run the file, report before/after:

```
make render-trend-list-matrix      # trend-list golden
make changes-index                 # CHANGES.md is rendered from docs/changes.d/, never hand-edited in a change PR
```

Decision rule: if the differing value **matches the intended change** (and the neighbours/docstring agree with the new value), the golden is stale — regenerate. If it **contradicts** its neighbours or the recipe's own docstring, suspect the code instead.

## Measure on the data path the test uses

If the test refreshes its data — a module fixture that downloads an upstream registry, a `live_sync`-style helper — then a probe against the **vendored** copy can disagree with the test and send you after a phantom. Re-run any claim through the same refresh the test performs before publishing it.

## Control shape

- **Fail on branch + pass on base**, same venv, same command, same data → in-diff by construction. `live-data` / `environment` requires the base to fail too.
- **Pass on both** → the branch fixed it, or the base already did; say which.
- Quote both results **and the durations**: near-identical runtimes prove both actually fetched/executed rather than one side short-circuiting on a cache.

Re-run the control against the base the branch will land on — a clean result measured at a superseded base proves nothing about the current one.

## Profile gates are host-sensitive

`scripts/check_agent_profiles.py` compares the tree against `~/.hermes/profiles/<profile>/`, so a host with drifted live profiles reports findings CI never sees. Separate the two:

```
HOME=/tmp/clean <venv>/bin/python -m pytest tests/test_agent_profiles.py   # the branch's own state
python3 scripts/check_agent_profiles.py check                              # with the real HOME
```

With an empty HOME the gate prints `tree checks only, LIVE RULEBOOKS NOT COMPARED`. Report the clean-home result as the branch's state and the real-home delta as host drift — never file the host's drift as a PR defect.
