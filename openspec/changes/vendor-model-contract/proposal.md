# The store is vendored together with the contract it is written against

## Why

`make sync-registry` copies upstream's `data/models.json` byte for byte and leaves the contract that
file must satisfy behind (issue #694):

```
data/models.json         635079 B   <- vendored
data/MODEL_CONTRACT.md     7350 B   <- not vendored
data/model_contract.json  16034 B   <- not vendored (JSON Schema, draft 2020-12)
```

`model_contract.json` says of itself: "JSON Schema that data/models.json must conform to … Enforced by
`scripts/validate.py`". llgenie's equivalent is four hand-written keys:

```python
for key in ("id", "name", "vram_tier", "engines"):
```

The upstream contract requires **15** keys per model row, a `pattern` on `id`, `minItems: 1` on
`formats` with `name` + `hf` per entry, `required` keys on every engine entry and an `enum` on its
`backend`. So a store that drops `formats`, or ships a format entry with no `hf` repo id, passes
`make sync-registry` and `make check-registry` today and fails only later inside the picker — the
`StopIteration` #687 measured on a store whose rows carry no usable `GGUF` row.

A contract change therefore arrives silently, buried in a 16k-line data diff, instead of as a diff of
the contract itself.

## What changes

- **The contract is vendored with the store.** `make sync-registry` fetches `data/model_contract.json`
  and `data/MODEL_CONTRACT.md` byte for byte alongside `models.json` and the README, and writes them
  only when they change, so a sync PR shows a contract edit as a diff of the contract.
- **`make check-registry` validates against that contract**, replacing the four-key check. The rules are
  read FROM the vendored schema, never restated in Python: the top-level `required` keys, each model
  row's `required` keys, the `id` `pattern`, `formats`' `minItems` and its items' `required` keys, the
  engine entry's `required` keys and its `backend` `enum`, and the engine-name `propertyNames` pattern.
  A contract edit that adds a required key is honoured on the next run without touching llgenie.
- **No new dependency.** Full JSON Schema means `jsonschema`, which is not in `tools/requirements*` and
  not in the test image; adding it changes the image's content hash, and a fork-head `pull_request`
  token cannot write GHCR packages (`denied: installation not allowed to Write organization package`,
  measured on PR #651). `ci-unit` would then have no image to pull and the PR would be red for a reason
  that is not the code. So the subset the contract actually uses — required keys, patterns, enums,
  minItems — is enforced data-driven from the schema; anything it expresses outside that subset is out
  of scope here and named on #694.

Honest limit: the schema does **not** restrict `formats[].name` to a format vocabulary, so this does not
catch #687's "`formats[].name` is not a format" class. That needs a rule, not a copy.

## Impact

- `scripts/sync_registry.py` — `UPSTREAM_CONTRACT` / `UPSTREAM_CONTRACT_DOC` / `VENDORED_CONTRACT*`,
  `sync()` writes all four files, `check()` calls the new `check_contract()` before the README checks.
- `data/model_contract.json`, `data/MODEL_CONTRACT.md` — the vendored copies (byte-identical to upstream).
- `Makefile` — the `sync-registry` / `check-registry` help lines say the contract is part of it.
- `tests/test_trend_pick.py` — a row missing a contract key, a bad `id`, a bad `backend`, a format entry
  without `hf`, and a missing vendored contract are each refused by name; the vendored copies are
  byte-identical to upstream (live); the real 23-model and 106-model stores pass.

Not in this change: the format-vocabulary rule (#687), the 101 data-pinned tests (#677), the 16 engines
with no skill or decision (#673), `data/search_contract.json` (a different consumer).
