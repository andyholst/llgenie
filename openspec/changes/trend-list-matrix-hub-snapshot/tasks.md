# trend-list-matrix-hub-snapshot

- [x] `scripts/model_engine_pick.py`: `HubSnapshotMissing`, `hub_snapshot_file()` / `LLGENIE_HUB_SNAPSHOT`, `hub_recording()`, the replay branch in `_hub_json` (no HTTP, no disk cache) and the explicit re-raise in `mlx_repos()` / `tensorfold_repos()`
- [x] `scripts/trend_list_matrix.py`: `--check` replays `tests/fixtures/hub-snapshot.json`, `--live` keeps the live comparison, and the render path records + writes the snapshot beside the fixture
- [x] `tests/fixtures/hub-snapshot.json` recorded from the same run that reproduces the committed `tests/fixtures/trend-list-matrix.json`
- [x] Observation: `--check` offline exits 0 and `git diff --stat tests/fixtures/trend-list-matrix.json` is empty
- [x] Observation: `--check` through an unroutable proxy (`HTTPS_PROXY=http://127.0.0.1:9`) exits 0, where it used to stall (exit 124)
- [x] Negative control: the gate pointed back at the live read reds `tests/test_hub_snapshot.py`, and restoring the replay path makes it green
- [x] `tests/test_hub_snapshot.py` (new module) green: offline reproduction, loud missing answer, MLX/TensorFold propagation, unchanged default live read, recording round trip + exclusivity
- [x] `make check-trend-list-matrix`, `make lint`, `make check-docs`, `make check-wiring` exit 0
- [x] `make test-unit` green (the gate `ci-unit` runs) — measured on the CI runner at head `ea17c715`: run `41139486704` job `linux / unit` → `3309 passed, 11899 deselected in 499.25s (0:08:19)`, and every later step of `make ci-unit` green; the local host run reached 67% with no failure before it stalled inside `tests/test_mac_trend_pick.py`'s unmarked live Hub read — the subject of the separately filed #1120, not this change
- [x] Docs: `docs/ARCHITECTURE.md` states the gate is hermetic, `agent-wiki/2026-10-30-trend-list-matrix-hub-snapshot.md`, `docs/changes.d/2026-10-30-trend-list-matrix-hub-snapshot.md`, `make changes-index`
- [x] `make openspec-validate NAME=trend-list-matrix-hub-snapshot` exits 0 and every box above is ticked — `Change 'trend-list-matrix-hub-snapshot' is valid`
