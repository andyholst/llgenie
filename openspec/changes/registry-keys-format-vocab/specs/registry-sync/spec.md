# registry-keys-format-vocab

## MODIFIED Requirements

### Requirement: a `formats` name that is not a format is not a loss

The `formats` loss check SHALL compare only the `formats[].name` values that are in the format vocabulary
the normaliser keeps (`scripts/sync_registry.FORMAT_VOCAB`, compared case-insensitively and returned in
its canonical spelling). A name outside that vocabulary is upstream display text, so its absence SHALL NOT
be a finding; a vocabulary format that disappears from a row SHALL still be a finding, named as today.

WHEN a row's non-format `formats` name is dropped by the normaliser
THEN the guard reports no loss for that row.
AND WHEN a vocabulary format (`GGUF`, `MLX`, …) disappears from a row
THEN the guard reports `formats lost [...]` naming it.

#### Scenario: a dropped non-format name is not a finding

Given a previous row with `formats[].name` "Qwen3.8-Flash-Next 125B" and a current row stating GGUF
When  the two stores are compared
Then  no finding names that dropped name.

- **Test:** `tests/test_registry_keys.py::test_a_dropped_non_format_name_is_not_a_loss`

#### Scenario: a dropped real format is still a finding

Given a previous row offering GGUF and MLX and a current row offering only MLX
When  the two stores are compared
Then  the finding names `formats lost ['GGUF']`.

- **Test:** `tests/test_registry_keys.py::test_a_dropped_real_format_is_still_a_loss`

#### Scenario: the real synced store passes the guard

Given the 2026-10-26 store produced by `make sync-registry` on this checkout
When  `make check-registry-keys` runs
Then  it reports `OK: additive only` with no LOSS finding.

- **Test:** CI job `registry-sync` step 9 (`make check-registry-keys`); measured on the host in the
  change's tasks.md.
