# 2026-10-26 — the openspec gate validates every active change

Issue: [#156](https://github.com/asimov-agent/llgenie/issues/156)
OpenSpec: `openspec/changes/openspec-validate-all`

## What was wrong

`ci-openspec` validated one hardcoded name (`NAME=ci-pipeline`) and `make loop` defaulted to
`NAME=llama-ai-tooling`, so the change a commit introduced was structurally validated only if someone
remembered to run it by hand.

## What changed

- `make openspec-validate-all` → `openspec validate --changes` (host on macOS, the openspec container
  elsewhere, like `openspec-validate`).
- `ci-openspec` runs it; `scripts/loop_harness.py` uses it unless `NAME` names one change.
- `tests/test_openspec_gate.py` reads the gate: CI uses the all-changes target and names no single
  change, and the loop's default is the all-changes one.

## What the gate immediately found

Two invalid changes, neither of which any CI run had noticed:

- `openspec-validate-all` itself (empty while being written — expected),
- **`engine-push-requires-binary`**: a `## ADDED Requirements` block with **no `#### Scenario:`**. A
  scenario was added, referencing the push tests that lock it.

## Verified

- `openspec validate --changes` → **208 passed, 0 failed** (was `206 passed, 2 failed`).
- `tests/test_openspec_gate.py` → 2 passed.
