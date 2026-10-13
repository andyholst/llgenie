"""Committed trending list for every (arch, vram, ram) `llgenie --matrix` takes.

The expected rows live in tests/fixtures/trend-list-matrix.json. They are
`matrix(registry, vram, ram, arch)` on the vendored registry: README order,
the highest t/s server on that architecture whose quant fits the card and the
RAM. A registry sync rewrites the fixture (`make render-trend-list-matrix`).
Until that rewrite lands, this test fails, and the pull-request diff is the
new list.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import model_engine_pick as mp  # noqa: E402
import trend_list_matrix as tlm  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "trend-list-matrix.json"
GOLDEN = json.loads(FIXTURE.read_text())
IDS = [tlm.case_key(arch, vram, ram) for arch, vram, ram in tlm.CASES]


def _expected(arch: str, vram: float, ram: float) -> list[dict]:
    key = (arch, vram, ram)
    for case in GOLDEN["cases"]:
        if (case["arch"], case["vram"], case["ram"]) == key:
            return case["rows"]
    raise AssertionError(f"no committed list for {tlm.case_key(arch, vram, ram)}")


def test_the_committed_matrix_is_the_vram_ram_arch_grid():
    """The fixture is one case per parameter, for this registry's generated_utc."""

    # Given the vendored registry and the parameter grid llgenie --matrix accepts

    # When the committed cases are read
    got = [(c["arch"], c["vram"], c["ram"]) for c in GOLDEN["cases"]]

    # Then they are that grid, and the stamp is the vendored registry
    assert got == tlm.CASES
    assert GOLDEN["generated_utc"] == mp.load_registry().get("generated_utc")
    assert len(IDS) == len(set(IDS))


def test_ram_changes_which_cuda_16gb_model_is_served():
    """Same card and architecture, two RAM sizes: the MoE fits only the larger one."""

    # Given the committed CUDA 16 GB lists
    tight = _expected("cuda", 16, 8)
    roomy = _expected("cuda", 16, 64)

    # When the first README row is read at each RAM size

    # Then 64 GB of RAM serves it on Strata, and 8 GB leaves a reason instead
    assert roomy[0]["model"] == tight[0]["model"]
    assert roomy[0]["server"] == "Strata" and roomy[0]["tps"] == 124.0
    assert tight[0]["server"] == "" and tight[0]["why"]


@pytest.mark.parametrize("arch,vram,ram", tlm.CASES, ids=IDS)
def test_trend_list_matches_the_committed_matrix(arch, vram, ram):
    """One (arch, vram, ram): the list matrix() returns is the committed list."""

    # Given the committed rows for this card, RAM, and architecture
    expected = _expected(arch, vram, ram)

    # When llgenie's matrix runs with those three arguments
    got = tlm.trend_rows(mp.load_registry(), vram, ram, arch)

    # Then the models and their fastest fitting server match, in README order
    assert got == expected
    served = [row for row in got if row["server"]]
    assert [row["model"] for row in got] == [row["model"] for row in expected]
    assert all(row["tps"] >= 0 for row in served)
