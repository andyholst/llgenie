---
name: quant-links-network-marker
about: the full-registry pick-matrix tests carry @pytest.mark.network, so make test-unit does no Hub I/O
status: active
---

# The live full-registry pick matrix is routed to the network seam (issue #1059)

## Proposal

`tests/test_pick_full_registry.py` is the FULL-registry pick matrix: every one of its tests calls
`_live_matrix()`, which runs `model_engine_pick.matrix()` against the LIVE Hugging Face repo trees,
probes the real quant links with `hub_probe.probe()`, or runs the wired `llgenie --matrix` CLI over
that live matrix. None of them carried `@pytest.mark.network`, so `scripts/unit_tests.py` (which
builds the hermetic gate as `-m "not network"`, issue #1000) ran all 11,879 of its nodes in
`make test-unit` — real Hub I/O inside a gate that is supposed to be hermetic.

Measured consequence: PR #932's `linux / unit` at head `0a710920` (run `41114385498`) died with
`HTTP Error 429: Too Many Requests [hf_auth]` — a red gate for a reason unrelated to the diff, and
the lesson a reader takes from it is "ignore a red local `test-unit`".

## Motivation

The #1000/#1002 split exists exactly for this: a test that reaches the real Hub carries the marker,
the hermetic gate deselects it, and `make test-unit-network` owns it. This file was missed on `main`
too, and the miss is invisible — nothing in the gate fails when a real call is unmarked, it simply
runs.

The offline half of the same behaviour is NOT lost: `tests/test_pick_matrix.py` and
`tests/test_pick_matrix_arch_perms.py` exercise `matrix()` over a synthetic registry with a stubbed
Hub tree and stay in the unit gate. So the assertions here move to the seam that owns live I/O;
none of them is deleted or weakened.

## Change

- `tests/test_pick_full_registry.py`: every test in the file (`test_pick_matrix_any_offer_is_a_real_fitting_hf_url`,
  `test_pick_matrix_real_quant_links_exist`, `test_pick_matrix_engine_supported_quants_catalog`,
  `test_pick_matrix_llgenie_cli_agrees_with_business_logic`,
  `test_pick_matrix_offers_only_engines_the_gap_says_have_an_image`,
  `test_pick_matrix_edge_case_golden`, `test_pick_matrix_edge_case_golden_ram`,
  `test_the_ram_ladder_never_shrinks_the_chosen_quant`) carries `@pytest.mark.network`, placed as the
  LAST decorator (immediately above `def`) so the two censuses that read the marker text see it. The
  module docstring states the routing and names the hermetic twins.
- `tests/test_check_model_links.py`: the #1000 routing census gains `test_pick_full_registry.py` in
  `DATA_PATH_FILES` and its eight live tests in `EXPECTED_NETWORK_TESTS`, so a marker removed here
  reds the census by file + test instead of silently returning a Hub call to the gate.
- No `scripts/unit_tests.py`, `tests/fixtures/unit-suite.json` or workflow change: the file stays
  discovered (it is neither excluded nor de-selected), and the existing `-m "not network"` /
  `--marker network` seam does the routing.
- `agent-wiki/` note + `docs/changes.d/` fragment (the index row lives in the fragment).

## Acceptance

- [x] Every test in `tests/test_pick_full_registry.py` carries `@pytest.mark.network` immediately
      above its `def`.
- [x] Under the gate's own expression (`-m "not network"`) that file collects ZERO tests; under
      `-m network` it collects all 11,879 nodes.
- [x] `tests/test_check_model_links.py::test_the_network_membership_of_the_hf_data_path_files_is_exact`
      pins the eight marks: removing one reds it, naming the file and the test.
- [x] `tests/test_network_marker.py` (execution pin + ownership pin) stays green.
- [x] `make test-unit` runs the gate with no Hub access from this file; no assertion is deleted.
- [x] `make lint`, `make check-docs`, `make check-wiring` and
      `make openspec-validate NAME=quant-links-network-marker` exit 0.
