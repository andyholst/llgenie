# vendor-model-contract

## ADDED Requirements

### Requirement: the sync vendors the contract the store is written against

`sync_registry.sync` SHALL fetch upstream's `data/model_contract.json` and `data/MODEL_CONTRACT.md`
byte for byte, write them to `data/model_contract.json` and `data/MODEL_CONTRACT.md`, and write nothing
when the store, the README and both contract files are unchanged. `make check-registry` SHALL require
the vendored contract and fail, naming `make sync-registry`, when it is absent.

WHEN the sync runs and upstream's contract differs from the vendored copy
THEN the contract files are rewritten and the sync reports the store as updated.

#### Scenario: the sync writes the contract next to the store

Given a source store, README and contract, and a destination with no contract
When  `sync()` runs
Then  `data/model_contract.json` and `data/MODEL_CONTRACT.md` exist and are byte-identical to the source.

- **Test:** `tests/test_trend_pick.py::test_sync_vendors_the_contract_next_to_the_store`

#### Scenario: an unchanged contract is not rewritten

Given a destination already holding the same store, README and contract
When  `sync()` runs again
Then  it reports the registry as unchanged and every file keeps its bytes.

- **Test:** `tests/test_trend_pick.py::test_sync_vendors_the_contract_next_to_the_store`

#### Scenario: a missing vendored contract fails the check

Given a store with no `data/model_contract.json` beside it
When  `check()` runs
Then  it fails, naming the missing contract file and `make sync-registry`.

- **Test:** `tests/test_trend_pick.py::test_check_refuses_a_store_with_no_vendored_contract`

### Requirement: the store is validated against the contract's own rules, read from the vendored schema

`check_contract(data, schema)` SHALL enforce, reading every rule FROM the schema and never restating
it: the top-level `required` keys, each model row's `required` keys, an engine-name
`propertyNames.pattern`, the engine entry's `required` keys, its `backend` `enum`, the model `id`
`pattern`, and `formats` (`minItems`, and its items' `required` keys). Every refusal SHALL name the
offending row.

WHEN a store violates a rule the vendored contract states
THEN the check fails, naming the model row and the field, and the sync does not land it.

#### Scenario: a model row missing a required key is refused by name

Given a contract requiring fifteen keys per model row
When  a store is checked whose first row has no `last_seen`
Then  the refusal names that row's `id` and `last_seen`.

- **Test:** `tests/test_trend_pick.py::test_check_contract_refuses_a_row_missing_a_contract_key`

#### Scenario: a bad id, a bad backend and a format without hf are each refused

Given a store whose `id` does not match the contract's pattern, whose engine `backend` is outside the
  contract's enum, or whose `formats[0]` has no `hf`
When  each is checked against the contract
Then  each is refused, naming the row and the field.

- **Test:** `tests/test_trend_pick.py::test_check_contract_refuses_a_bad_id_a_bad_backend_and_a_format_without_hf`

#### Scenario: the real stores satisfy the contract

Given the committed store and a freshly synced store
When  each is checked against the vendored contract
Then  neither is refused.

- **Test:** `tests/test_trend_pick.py::test_the_vendored_contract_is_upstreams_and_the_store_satisfies_it`

### Requirement: a contract edit is a diff, not a silent data change

The vendored `data/model_contract.json` and `data/MODEL_CONTRACT.md` SHALL be byte-identical to
upstream's copies, so a contract edit shows up as a diff of the contract in the sync PR.

WHEN upstream's contract changes
THEN the sync PR's diff contains the contract change itself.

#### Scenario: the vendored copies match upstream byte for byte

Given the vendored contract files and the live upstream copies
When  both are read
Then  each pair is byte-identical.

- **Test:** `tests/test_trend_pick.py::test_the_vendored_contract_is_upstreams_and_the_store_satisfies_it`
