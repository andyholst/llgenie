# openspec-validate-all — proposal

Issue: [#156](https://github.com/asimov-agent/llgenie/issues/156)

## Why

`ci-openspec` validated **one hardcoded change name** (`NAME=ci-pipeline`), and `make loop` defaulted to
`NAME=llama-ai-tooling`, so the change a commit actually introduces was never structurally validated —
except by whoever remembered to run it. A change could land with an invalid spec.

## What Changes

- **`make openspec-validate-all`** (new): `openspec validate --changes` — every ACTIVE change. Host on
  macOS, the openspec container elsewhere, like `openspec-validate`.
- **`ci-openspec`** runs it instead of `NAME=ci-pipeline`.
- **`scripts/loop_harness.py`**: the openspec stage validates every change when `NAME` is not given, and
  one change when it is.

## Benefit

The gate covers the change under review without anyone naming it — and it immediately found two: this
change's own sibling `engine-push-requires-binary` had a requirement with **no scenario** (fixed here),
which no CI run had ever noticed.
