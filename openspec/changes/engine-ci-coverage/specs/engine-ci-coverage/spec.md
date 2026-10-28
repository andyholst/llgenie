# engine-ci-coverage

## ADDED Requirements

### Requirement: a shipped engine is built by CI, or says why it is not an image

`make ci-unit` MUST fail, naming the engine, when a skill that is `servable: true` with `linux` in
`os` has no buildable CI cell — every params variant is either in `engine_image.DISABLED` or outside
`CI_VARIANTS` — and the engine is not recorded in `KNOWN_UNBUILT`. A skill that is `servable: false`,
`servable: via`, or has no `linux` in `os` MUST pass without an exception, because it is deliberately
not a container image.

WHEN a shipped servable linux engine has no buildable CI cell
THEN `make check-engine-coverage` exits non-zero and names the engine, its cells and why each is dropped.

#### Scenario: the only cell is disabled

- **Given** a skill with `servable: true`, `os: [linux]`, and one committed params cell that
  `engine_image.DISABLED` drops
- **When** `make check-engine-coverage` runs
- **Then** the gate fails and names the engine, the cell and the disabled reason
- **Test:** `tests/test_engine_coverage.py::test_a_cell_the_matrix_drops_leaves_the_engine_unbuilt`

#### Scenario: the variant is not one the matrix builds

- **Given** a servable linux skill whose only params variant is outside `CI_VARIANTS`
- **When** the verdict runs over it
- **Then** the engine is `unbuilt` and the reason says the variant is not a CI variant
- **Test:** `tests/test_engine_coverage.py::test_a_variant_outside_the_ci_variants_is_not_a_cell`

#### Scenario: one buildable cell covers the engine

- **Given** a servable linux skill with a `cpu` params cell, nothing dropped
- **When** the verdict runs over it
- **Then** the engine is `built` with `cpu` as its reason
- **Test:** `tests/test_engine_coverage.py::test_one_buildable_cell_covers_the_engine`

#### Scenario: deliberately imageless engines pass

- **Given** a `servable: via` skill, a `servable: false` skill, and a skill whose `os` has no `linux`
- **When** each is classified
- **Then** each is `not-an-image` with its own reason and none needs an exception
- **Test:** `tests/test_engine_coverage.py::test_deliberately_imageless_engines_pass`

### Requirement: an exception cannot outlive the gap it records

`KNOWN_UNBUILT` MUST carry, per engine, the reason and the issue that tracks it. A `KNOWN_UNBUILT`
entry whose engine is now `built` or `not-an-image`, or whose skill no longer exists, MUST fail the
gate as stale so the record cannot hide a resolved gap.

WHEN a `KNOWN_UNBUILT` engine becomes buildable
THEN `make check-engine-coverage` fails and says the exception is stale.

#### Scenario: a new unbuilt engine fails, naming it

- **Given** an unbuilt engine and no exception recorded for it
- **When** the gate looks for findings
- **Then** it fails and names the engine, the reason and `#771`
- **Test:** `tests/test_engine_coverage.py::test_a_new_unbuilt_engine_fails_the_gate_naming_it`

#### Scenario: a stale exception fails

- **Given** an engine that is `built` and an exception that still records it
- **When** the gate runs
- **Then** it fails and says the exception is stale
- **Test:** `tests/test_engine_coverage.py::test_a_stale_exception_fails_the_gate`

#### Scenario: the committed tree satisfies the gate

- **Given** the real skills tree and the committed params
- **When** `make check-engine-coverage` runs
- **Then** it exits 0, so a red run on a branch means a real new gap
- **Test:** `tests/test_engine_coverage.py::test_the_real_tree_is_green`
