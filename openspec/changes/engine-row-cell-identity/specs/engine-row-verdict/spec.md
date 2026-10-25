# engine-row-verdict

## ADDED Requirements

### Requirement: One code path decides every engine row

An engine row's flag verdict SHALL be decided by the product function
(`scripts/engine_image.py::binary_file_works`), which reads the cell's manifest entry, probes every documented
flag plus every flag a user types inside the image, and decides with that cell's engine id and variant so the
`DEVICE_ONLY` exemption applies exactly where it is declared. The engine-row test SHALL call that function and
SHALL NOT carry a probe, a parser or a decider call of its own: a copy of the pipeline cannot inherit a change
made to it, which is how the four device-only cells went red while the CLI accepted them.

WHEN an engine image's row is verified
THEN the verdict comes from `binary_file_works` with the cell's engine id and variant,
AND  the engine-row test carries no probe, parser or decider of its own.

#### Scenario: the engine row decides through the product function

Given a built engine image and its manifest entry
When  the engine row is verified
Then  `binary_file_works(spec)` returns the verdict, and its `[engine-image]` table is the row's evidence.

- **Test:** `tests/test_engine_binary_flags.py::test_the_engine_row_test_reuses_the_product_probe`

#### Scenario: a device-only cell is exempt and any other cell that answers nothing is red

Given an engine whose flags cannot answer without its device, and one whose flags answer
When  each image's row is verified
Then  the `DEVICE_ONLY` cell is accepted with its measured reason and any other cell that answers nothing is
      red — the rule `scripts/engine_image.py` enforces for every row.

- **Test:** `tests/test_engine_gate_strict.py::test_a_device_verdict_needs_the_cell_identity`
- **Test:** `tests/test_engine_gate_strict.py::test_the_gate_report_shows_the_detect_that_will_prove_the_version`
