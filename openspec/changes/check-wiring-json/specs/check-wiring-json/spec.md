# check-wiring-json

## ADDED Requirements

### Requirement: the json subcommand emits a complete, serialisable graph

`scripts/check_wiring.py json` MUST exit 0 and print JSON containing exactly the keys `reachable`,
`named_by_target` and `workflow_targets`, with every value a list.

WHEN a script asks for the wiring graph as JSON
THEN it receives valid JSON with those three keys and no sets.

#### Scenario: the subcommand answers on the real tree

- **Given** the real checkout
- **When** `scripts/check_wiring.py json` runs
- **Then** it exits 0, `json.loads` succeeds, the keys are exactly the three, and every value is a list
- **Test:** `tests/test_wiring.py::test_the_json_subcommand_is_valid_json_with_the_three_keys`

#### Scenario: the graph owns the key it is asked for

- **Given** `graph(root)`
- **When** its dict is read
- **Then** `named_by_target` is present, so the `json` and `check` paths share one computation
- **Test:** `tests/test_wiring.py::test_the_json_subcommand_is_valid_json_with_the_three_keys`
