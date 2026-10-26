# 2026-10-26 — a help line's CI claim must match what CI does

Issue: [#239](https://github.com/asimov-agent/llgenie/issues/239)
OpenSpec: `openspec/changes/install-ci-claim`

## What was wrong

`make test-install-ci`'s `##` line claimed "(CI linux / macos pipelines)" while no CI job called it. The
claim guard did not fire because the target also carried a decision in
`tests/fixtures/host-only-wiring.json` whose reason said *"its help line no longer claims the pipelines
run it"* — which was false. A recorded entry short-circuits the claim check, so the decision and the
help line had drifted apart without anyone noticing.

## What changed

- The `##` line now says what the target is (a LOCAL one-container acceptance) and where CI covers the
  same flow (`make ci-install`'s stages).
- Its decision entry is deleted — with the claim gone it is exactly the dead prose the guard now refuses.
- `check_wiring.py` treats a decision whose help line no longer claims CI coverage as **stale**
  ("delete the entry"), which closes the loop.

## Verified

```
make check-wiring → OK 201 documents (124 tests, 77 scripts), 197 run in CI, 4 host-only
the stale-decision rule on the pre-fix state → "`make test-install-ci` no longer claims CI coverage in
its help line, so the entry is stale — delete it" (Error 1)
tests/test_wiring.py → 11 passed
```
