## ADDED Requirements

### Requirement: full-registry-pick-matrix-is-network-routed

Every test in `tests/test_pick_full_registry.py` SHALL carry `@pytest.mark.network`, because every
one of them reaches the live Hugging Face Hub (`_live_matrix` -> `model_engine_pick.matrix`, the
`hub_probe` link probe, or the wired `llgenie --matrix` CLI over that live matrix). The hermetic
unit gate (`scripts/unit_tests.py`, `-m "not network"`, issue #1000) SHALL therefore collect no node
from that file, and the network pipeline (`make test-unit-network`, `-m network`, issue #1002) SHALL
collect all of them. No assertion SHALL be deleted or weakened to achieve the routing.

#### Scenario: the hermetic gate collects none of the live matrix

- **Given** the gate's own selection (every discovered `tests/test_*.py` minus the dated exclusions
  in `tests/fixtures/unit-suite.json`)
- **When** pytest collects it with the gate's expression `-m "not network"`
- **Then** `tests/test_pick_full_registry.py` contributes zero collected nodes
- **And** the same expression deselects rather than errors, so `make test-unit` still runs
- **Test:** CI job `unit` -> `make test-unit` -> `scripts/unit_tests.py run` (`-m "not network"`);
  observed with `pytest tests/test_pick_full_registry.py --collect-only -q -m "not network"` ->
  `no tests collected (11879 deselected)`

#### Scenario: the network pipeline owns every mark

- **Given** the same selection
- **When** pytest collects it with `-m network` (the `make test-unit-network` seam)
- **Then** every test of `tests/test_pick_full_registry.py` is collected, parametrizations included
- **Test:** `tests/test_network_marker.py::test_the_network_pipeline_owns_the_marks`

#### Scenario: the gate never executes a network-marked node

- **Given** the markers on the live matrix
- **When** the gate's collect runs under `-m "not network"`
- **Then** no collected node belongs to a `@pytest.mark.network`-decorated test
- **Test:** `tests/test_network_marker.py::test_the_unit_gate_executes_zero_network_marked_tests`

#### Scenario: a removed marker is a named red, not a silent gate regression

- **Given** the #1000 routing census over the data-path files
- **When** the marker is removed from one live-matrix test
- **Then** the census fails naming that file and test in `network-membership drift`
- **And** with every marker present the census passes
- **Test:** `tests/test_check_model_links.py::test_the_network_membership_of_the_hf_data_path_files_is_exact`

#### Scenario: the offline pick-matrix coverage stays in the gate

- **Given** `tests/test_pick_matrix.py` and `tests/test_pick_matrix_arch_perms.py`, which drive
  `matrix()` over a synthetic registry with a stubbed Hub tree
- **When** the hermetic gate runs
- **Then** both files remain collected and green, so routing the live file loses no offline assertion
- **Test:** `tests/test_pick_matrix.py` and `tests/test_pick_matrix_arch_perms.py` in
  `make test-unit`
