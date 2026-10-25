# engine-gate-strict

## ADDED Requirements

### Requirement: at least one probed flag must exit 0

`decide()` SHALL fail an engine cell when none of its probed flags exits 0, whatever its `probe` policy. The
`probe: device` policy SHALL NOT be an exemption by itself: it may only carry a cell named in `DEVICE_ONLY`,
and every `DEVICE_ONLY` entry SHALL state the measured reason and its tracking issue.

WHEN every probed flag of a cell exits non-zero
THEN the cell is red, unless its `(engine, variant)` is named in `DEVICE_ONLY`.

#### Scenario: an unlisted device-policy cell is red

- **Given** a cell whose documented and typed flags all exit 1, with `probe: device`
- **When** `decide()` runs for a cell that is not in `DEVICE_ONLY`
- **Then** the verdict is not ok, and the failure names `DEVICE_ONLY` and the issue with both remedies
- **Test:** `tests/test_engine_gate_strict.py::test_a_device_policy_cell_that_answers_nothing_is_red_unless_it_is_listed`

#### Scenario: a listed cell passes and says why

- **Given** the same all-failing probes on a cell that IS in `DEVICE_ONLY`
- **When** `decide()` runs
- **Then** the verdict is ok and its note quotes the exempting reason (with the issue)
- **Test:** `tests/test_engine_gate_strict.py::test_a_listed_cell_is_exempt_but_says_why`

#### Scenario: the exemption is pinned to the measured cells

- **Given** the committed `DEVICE_ONLY`
- **When** its keys are read
- **Then** they are exactly the four cells run 40204145334 measured, and each reason is issue-tagged
- **Test:** `tests/test_engine_gate_strict.py::test_the_exemption_list_is_exactly_the_measured_cells`

#### Scenario: a flags-policy cell never inherits the exemption

- **Given** a listed cell whose manifest says `probe: flags`
- **When** `decide()` runs
- **Then** it is red — the exemption is device-policy only
- **Test:** `tests/test_engine_gate_strict.py::test_the_exemption_never_applies_to_a_flags_policy_cell`

### Requirement: a detect line must prove a version shape

The image's `entrypoint.sh detect` output MUST prove a version: a semantic version, or `pin <sha7…>` for an
engine whose upstream prints no version at all. A timestamped server log line (`0.00.000.272 I srv …`) and the
placeholder `0.0.0` MUST be refused, and the failure MUST name what was seen.

WHEN `detect` prints a line
THEN `version_proof()` returns the version token, or the cell is red.

#### Scenario: a log timestamp is not a version

- **Given** `installed 0.00.000.272 I srv  llama_server: initializing ...` (what the laurentzuijdwijk fork's
  `--version` prints)
- **When** the proof is read
- **Then** it is empty, so the cell fails
- **Test:** `tests/test_engine_gate_strict.py::test_a_version_must_look_like_a_version`

#### Scenario: the 0.0.0 placeholder is not a version

- **Given** `installed 0.0.0` (sglang's rocm wheel via `sglang.__version__`)
- **When** the proof is read
- **Then** it is empty
- **Test:** `tests/test_engine_gate_strict.py::test_the_log_stamp_and_the_placeholder_are_named_in_the_rule`

#### Scenario: a pin is an accepted identity

- **Given** `installed pin 3c75be02f450`
- **When** the proof is read
- **Then** it returns `pin 3c75be02f450`
- **Test:** `tests/test_engine_gate_strict.py::test_a_version_must_look_like_a_version`

### Requirement: the two broken detections report a real identity

`sglang`'s `detect` MUST read the installed distribution's version (its own `__version__` is `0.0.0` in the
rocm wheel), and `llama.cpp-laurentzuijdwijk`'s `detect` MUST select its `version:` line rather than the log stamp
that precedes it.

WHEN the committed params and binaries are read
THEN `sglang` uses `importlib.metadata` and the fork documents `--help` only and detects `echo "pin <sha>"`.

#### Scenario: the two detects are fixed at the source

- **Given** `containers/engines/params/{sglang,llama.cpp-laurentzuijdwijk}.json` and `binaries.json`
- **When** their detect commands and flags are read
- **Then** sglang no longer mentions `sglang.__version__`, and the fork's flags are `["--help"]` with a
  `pin <sha>` detect
- **Test:** `tests/test_engine_gate_strict.py::test_the_two_broken_detects_no_longer_produce_a_false_version`
