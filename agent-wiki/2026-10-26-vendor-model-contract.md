# 2026-10-26 — the store is vendored with the contract it is written against

Implements issue #694 (OpenSpec change `vendor-model-contract`).

## What was wrong (measured)

`make sync-registry` copied upstream's `data/models.json` byte for byte and left the contract behind:

```
andyholst/trending-local-llms  data/models.json         635079 B   vendored
                               data/model_contract.json  16034 B   not vendored (JSON Schema 2020-12)
                               data/MODEL_CONTRACT.md     7350 B   not vendored
```

`model_contract.json` describes itself as the schema `data/models.json` must conform to, enforced
upstream by `scripts/validate.py`. llgenie's own check was four keys (`id`, `name`, `vram_tier`,
`engines`); the contract requires fifteen per model row, a `pattern` on `id`, `minItems: 1` on `formats`
with `name` + `hf` per entry, `required` keys on every engine entry and an `enum` on its `backend`. A
store that drops `formats`, or ships a format entry with no `hf`, passed both `sync-registry` and
`check-registry` and failed later inside the picker — the `StopIteration` #687 measured. A contract edit
arrived as a 16k-line data diff, never as a diff of the contract.

## What was decided

- Vendor `data/model_contract.json` and `data/MODEL_CONTRACT.md` byte for byte in `sync()`, alongside the
  store and the README, written only when they change.
- `check()` validates the store against the **vendored schema**, reading the rules from it: `required`
  (top level, model rows, format entries, engine entries), `id` `pattern`, engine-name
  `propertyNames.pattern`, `backend` `enum`, `formats.minItems`. A contract edit that adds a required key
  is honoured without touching llgenie.
- **No `jsonschema` dependency.** It is not in `tools/requirements*` and not in the test image; adding it
  changes the image content hash, and a fork-head `pull_request` token cannot write GHCR packages
  (measured on PR #651), so `ci-unit` would have no image to pull and the PR would be red for a reason
  that is not the code. The subset the contract actually uses is enforced data-driven instead; anything
  outside it is named on #694, not hidden.

Honest limit, in the issue and the PR: the schema leaves `formats[].name` a free `string`, so this does
**not** catch #687's "`formats[].name` is not a format" class — that needs a rule, not a copy.

## Verified

- `make check-registry` on the committed 23-model store: `OK … contract satisfied, README order
  matches, links answer`.
- The freshly synced 106-model store (2026-10-26T14:06:43Z) checked against the vendored contract and
  its README: `contract satisfied, README order matches`.
- New tests: the sync writes all four files and is idempotent; a store with no vendored contract is
  refused with the command that provisions it; a row missing `last_seen`, a bad `id`, a backend outside
  the enum and a `formats[0]` without `hf` are each refused by name; the vendored copies equal upstream
  byte for byte and the vendored store satisfies them.
- `make test-unit` and `make openspec-validate NAME=vendor-model-contract` recorded in `tasks.md`.

## Status

Implementation complete on `feat/vendor-model-contract`. Not in this change: the format-vocabulary rule
(#687), the 101 data-pinned tests that still stop the weekly sync (#677), the 16 undecided engines
(#673), and `data/search_contract.json` (a different consumer).
