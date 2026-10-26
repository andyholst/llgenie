# refiner-dry-no-write

## ADDED Requirements

### Requirement: a dry pick writes nothing

`issue_refiner.pick(..., dry=True)` MUST NOT write the agent's input file (or anything else) into the
working tree. It MUST report the issue it would refine and the path it would write.

WHEN the refiner previews a pick
THEN the working tree is unchanged and the run says where the file would have gone.

#### Scenario: DRY leaves the tree clean

- **Given** an open issue the refiner would pick
- **When** `pick()` runs with `dry=True`
- **Then** no `refine-in.md` is created and the output says "nothing written"
- **Test:** `tests/test_issue_refiner.py::test_dry_run_writes_nothing_into_the_checkout`

#### Scenario: the real run still writes

- **Given** the same issue
- **When** `pick()` runs with `dry=False`
- **Then** the file exists and carries the rendered input
- **Test:** `tests/test_issue_refiner.py::test_dry_run_writes_nothing_into_the_checkout`
