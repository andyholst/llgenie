# install-ci-claim — proposal

Issue: [#239](https://github.com/asimov-agent/llgenie/issues/239)

## Why

`make test-install-ci`'s `##` help line claimed "(CI linux / macos pipelines)" while **no CI job
called it** — the very lie the claim guard exists to catch. It slipped through because the target also
carried a recorded decision in `tests/fixtures/host-only-wiring.json` whose reason said *"its help line
no longer claims the pipelines run it"* — which was not true. A recorded entry short-circuits the claim
check, so the mismatch was invisible: the decision and the help line drifted apart and both stopped
describing the tree.

## What Changes

- **`Makefile`** — `test-install-ci`'s `##` line says what it is: a LOCAL one-container acceptance
  (`make install` → `test-built-engine` → install tests → "hi" → trend pick → uninstall), and that CI
  covers the same flow as separate stages through `make ci-install`.
- **`tests/fixtures/host-only-wiring.json`** — its entry is deleted: with the claim gone it is exactly
  the dead prose the guard now refuses.
- **`scripts/check_wiring.py`** — a recorded target decision whose help line no longer claims CI
  coverage is **stale**: `delete the entry`. This is the rule that closes the loop the issue exposed.
- **`tests/test_wiring.py`** — a case for the stale decision.

## Benefit

The help a human reads at `make help` time matches what CI does, and a recorded decision can no longer
rot into prose that contradicts the tree.
