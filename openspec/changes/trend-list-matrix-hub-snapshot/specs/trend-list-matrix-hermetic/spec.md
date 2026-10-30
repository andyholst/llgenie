## ADDED Requirements

### Requirement: the-trend-list-matrix-gate-is-hermetic

`python3 scripts/trend_list_matrix.py --check` SHALL replay the recorded Hub answers in
`tests/fixtures/hub-snapshot.json` instead of reaching the Hub, so `model_engine_pick.matrix()` on the
vendored registry is a pure function: no HTTP request, no Hub disk-cache read or write, and a URL the
recording does not carry SHALL raise `model_engine_pick.HubSnapshotMissing` naming that URL rather than
falling back to the network. `--check --live` SHALL keep the pre-existing live comparison, and with
neither a recording nor the flag set, `_hub_json` SHALL remain the live read it was.

WHEN the hermetic unit gate's `make check-trend-list-matrix` runs on a host with no route,
THEN it SHALL exit 0 and reproduce `tests/fixtures/trend-list-matrix.json` byte-identically.

#### Scenario: the gate reproduces the committed matrix with no route

- **Given** the committed recording `tests/fixtures/hub-snapshot.json` and a process in which every
  HTTP entry point (`urllib.request.urlopen`) raises
- **When** `python3 scripts/trend_list_matrix.py --check` runs
- **Then** it exits 0 and prints the fixture name and the 81 cases
- **And** the bytes it built equal the committed fixture's bytes, so `git diff --stat` is empty
- **Test:** `tests/test_hub_snapshot.py::test_the_check_reproduces_the_fixture_with_no_route`

#### Scenario: a URL absent from the recording is loud, never a live call

- **Given** a recording missing one URL the matrix reads
- **When** a pure `matrix()`/`trend_rows()` build runs under it
- **Then** `HubSnapshotMissing` is raised naming the URL, and no HTTP request is attempted
- **Test:** `tests/test_hub_snapshot.py::test_a_url_missing_from_the_recording_is_loud`

#### Scenario: the MLX and TensorFold searches cannot swallow a gap

- **Given** a recording missing the MLX search answer for a model
- **When** `mlx_repos()` (and `tensorfold_repos()`) run under it
- **Then** `HubSnapshotMissing` propagates instead of the broad `except Exception` returning `[]`
- **Test:** `tests/test_hub_snapshot.py::test_the_mlx_and_tensorfold_searches_propagate_a_gap`

#### Scenario: the default live read is unchanged

- **Given** no recording and no flag
- **When** `_hub_json` is asked for a URL and a local HTTP server answers it
- **Then** the real `hub_open` transport is used and the answer is returned unchanged
- **Test:** `tests/test_hub_snapshot.py::test_the_default_path_is_still_the_live_read`

#### Scenario: the render path records what the gate replays

- **Given** a live read of one URL inside `hub_recording()`
- **When** the recording is written to a snapshot file and replayed by `hub_snapshot_file()`
- **Then** both spellings of that URL's answer are equal, so a render can never publish a fixture the
  gate cannot rebuild
- **And** entering `hub_recording()` while a recording is replayed is refused, because one source of
  Hub answers is the point
- **Test:** `tests/test_hub_snapshot.py::test_a_recording_round_trips_and_replay_is_exclusive`
