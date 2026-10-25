# engine-row-verdict

## ADDED Requirements

### Requirement: One code path decides every engine row, and it knows the cell

An engine row's flag verdict SHALL be decided by the product function
(`scripts/engine_image.py::binary_file_works`), which SHALL pass the cell's own engine id and variant to the
decider so the `DEVICE_ONLY` exemption applies to exactly the cells listed there. A test SHALL NOT re-implement
the probe or call the decider on its own, and SHALL NOT lose the cell identity. A `DEVICE_ONLY` cell whose
flags all fail SHALL pass only with its own identity (its version comes from the image's `detect` entrypoint);
the same verdicts on any other cell, or with an empty identity, SHALL be red and the failure SHALL name the
cell.

WHEN an engine image's row is verified
THEN the verdict comes from the product function with that cell's engine id and variant,
AND  a cell whose flags cannot answer without its device passes only if it is named in `DEVICE_ONLY`.

#### Scenario: the four device-only cells pass through the product function

Given the manifest's documented flags for a `DEVICE_ONLY` cell, and a probe in which every flag failed
When  the engine row is verified
Then  the verdict is ok because the cell is exempt, and it says the version comes from `detect`.

- **Test:** `tests/test_engine_binary_flags.py::test_every_device_only_cell_is_exempt_with_its_own_identity`

#### Scenario: the same verdicts with no identity are red

Given the same all-flags-failed verdicts
When  they are decided with an empty engine and variant
Then  the verdict is a failure, and the failure names the empty cell as not on the exemption list.

- **Test:** `tests/test_engine_binary_flags.py::test_an_empty_cell_identity_is_never_exempt`

#### Scenario: the engine row does not re-implement the probe

Given the engine row's test file
When  its text is read
Then  it calls `binary_file_works` and carries no `BINARY_PROBE` or `decide(` call of its own.

- **Test:** `tests/test_engine_binary_flags.py::test_the_engine_row_test_reuses_the_product_probe`
