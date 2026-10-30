# quant-links-network-marker

- [x] `tests/test_pick_full_registry.py`: `@pytest.mark.network` as the last decorator on all eight live tests (the quant-links test named in #1059 plus its live siblings), and the module docstring states the routing and names the hermetic twins
- [x] `tests/test_check_model_links.py`: the #1000 census gains the file in `DATA_PATH_FILES` and its eight tests in `EXPECTED_NETWORK_TESTS`
- [x] Observation: `pytest tests/test_pick_full_registry.py --collect-only -m "not network"` -> `no tests collected (11879 deselected)`; `-m network` -> `11879 tests collected`
- [x] Negative control: removing one marker reds `test_the_network_membership_of_the_hf_data_path_files_is_exact` with `network-membership drift` naming the file and test; restored, that file plus `tests/test_network_marker.py` = 14 passed
- [x] `make test-unit` green at head `5d56d7ca`: `3160 passed, 11892 deselected` (33:34) — the live matrix contributes no node, no Hub I/O
- [x] `make lint`, `make check-docs`, `make check-wiring` exit 0
- [x] `make openspec-validate NAME=quant-links-network-marker` exits 0 and `make openspec-tasks-check` reports every task checked
- [x] `agent-wiki/` note + `docs/changes.d/` fragment, `CHANGES.md` re-rendered with `make changes-index`
