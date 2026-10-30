# 2026-10-30 — issue #1059: the live full-registry pick matrix is routed to the network seam

## What was wrong

`tests/test_pick_full_registry.py` is the FULL-registry pick matrix: `_live_matrix()` runs
`model_engine_pick.matrix()` against the LIVE Hugging Face repo trees, `hub_probe.probe()` answers a
real ranged GET per quant link, and the wired `llgenie --matrix` CLI is run over that same live
matrix. Its tests carried no `@pytest.mark.network`, and `scripts/unit_tests.py` builds the hermetic
gate as `-m "not network"` (issue #1000) — so `make test-unit` executed all of it, real Hub I/O
inside a gate that promises none.

Measured: PR #932's `linux / unit` at head `0a710920` (run `41114385498`) failed with
`HTTP Error 429: Too Many Requests [hf_auth]`. A red gate for a reason unrelated to the diff is how
people learn to ignore a red `test-unit`.

## What was measured before the change

The file is discovered (`python3 scripts/unit_tests.py list`) and the gate's argv ends with
`-m not network …` (`python3 scripts/unit_tests.py argv`), so nothing about the marker mechanism was
missing — only the marks.

## What the change is

- `@pytest.mark.network` on all EIGHT live tests of the file, placed as the LAST decorator (directly
  above `def`) so both marker-text censuses see it:
  `test_pick_matrix_any_offer_is_a_real_fitting_hf_url`,
  `test_pick_matrix_real_quant_links_exist` (the one #1059 names),
  `test_pick_matrix_engine_supported_quants_catalog`,
  `test_pick_matrix_llgenie_cli_agrees_with_business_logic`,
  `test_pick_matrix_offers_only_engines_the_gap_says_have_an_image`,
  `test_pick_matrix_edge_case_golden`, `test_pick_matrix_edge_case_golden_ram`,
  `test_the_ram_ladder_never_shrinks_the_chosen_quant`.
- `tests/test_check_model_links.py`: the #1000 routing census gains the file in `DATA_PATH_FILES`
  and those eight names in `EXPECTED_NETWORK_TESTS` — a removed marker is now a named red, not a
  silent return of Hub I/O to the gate.
- No `unit_tests.py`, `tests/fixtures/unit-suite.json` or workflow change: the file stays
  discovered, and the existing `-m "not network"` / `--marker network` seam routes it.

## The observation (not the marker text)

```
$ pytest tests/test_pick_full_registry.py --collect-only -q -m "not network"
no tests collected (11879 deselected) in 0.40s     # the gate's expression, zero nodes

$ pytest tests/test_pick_full_registry.py --collect-only -q -m network
11879 tests collected in 0.36s                     # the network pipeline owns them all
```

Negative control for the census: with one marker removed the census failed naming the file and the
test — `AssertionError: network-membership drift: … actual-marks … 'test_pick_full_registry.py'` —
and the restored file reports `14 passed` for `tests/test_check_model_links.py` +
`tests/test_network_marker.py`.

## Decisions

- **No assertion was deleted or weakened.** The offline half of this behaviour already lives in
  `tests/test_pick_matrix.py` + `tests/test_pick_matrix_arch_perms.py` (synthetic registry, stubbed
  Hub tree), which stay in the unit gate; the live file keeps every assertion and moves to the seam
  that owns live I/O.
- **Marker per test, not a module-level `pytestmark`.** The two censuses (`test_network_marker.py`,
  `test_check_model_links.py`) read the marker's own line and the `def` beneath it; a module-level
  mark would route the tests but leave both pins blind, which is how the next real call escapes.
- **The census was extended, not left alone.** Without it, deleting a marker here would be invisible
  and the file would quietly re-enter the gate — the exact defect #1059 reports.

Issue: #1059
