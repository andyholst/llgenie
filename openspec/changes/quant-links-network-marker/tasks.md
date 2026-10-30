# quant-links-network-marker

- [x] `tests/test_pick_full_registry.py`: `@pytest.mark.network` as the last decorator on all eight live tests (the quant-links test named in #1059 plus its live siblings), and the module docstring states the routing and names the hermetic twins
- [x] `tests/test_check_model_links.py`: the #1000 census gains the file in `DATA_PATH_FILES` and its eight tests in `EXPECTED_NETWORK_TESTS`
- [ ] Observation: `pytest tests/test_pick_full_registry.py --collect-only -m "not network"` -> `no tests collected (11879 deselected)`; `-m network` -> `11879 tests collected`
- [ ] Negative control: removing one marker reds `test_the_network_membership_of_the_hf_data_path_files_is_exact` with `network-membership drift` naming the file and test
- [ ] `tests/test_check_model_links.py` + `tests/test_network_marker.py` green (14 passed)
- [ ] `make test-unit`, `make lint`, `make check-docs`, `make check-wiring` green
- [ ] `make openspec-validate NAME=quant-links-network-marker` exits 0
- [ ] `agent-wiki/` note + `docs/changes.d/` fragment, `CHANGES.md` re-rendered with `make changes-index`
