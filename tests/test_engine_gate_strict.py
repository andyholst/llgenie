"""The engine gate must be falsifiable: no flag answered = red, and a version must look like one (#625).

Audited from run 40204145334 (29/29 green):

  * `vllm/cuda`, `vllm/rocm`, `tensorrt-llm/cuda` and `mlx/cuda` had EVERY probe at exit 1 and were still
    green, because `decide()` returned ok for any `probe: device` cell;
  * `llama.cpp-laurentzuijdwijk` reported `installed 0.00.000.272 I srv  llama_server: initializing ...` and
    `sglang/rocm` reported `installed 0.0.0`, and `test_image()`'s `\\d+\\.\\d+` search accepted both.

These tests pin both halves: the exemption is a NAMED list with a reason, and a version must be a version.
No docker, no mocks of the product — `decide` and `version_proof` are the product's own pure functions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import engine_image as ei  # noqa: E402


def _verdicts(**flags: int) -> dict:
    """Per-flag probe results: exit code per flag, one byte of output so 'answered' means exit 0."""
    return {f: {"rc": rc, "bytes": 1, "output": ("x" if rc == 0 else "boom")} for f, rc in flags.items()}


# --- the version half -------------------------------------------------------------------------------

def test_a_version_must_look_like_a_version():
    """A semver or a declared pin is a version; a log timestamp and `0.0.0` are not (issue #625)."""

    # Given the shapes measured in run 40204145334
    accepted = {
        "sglang 0.5.21": "0.5.21",
        "vllm/cpu: installed 0.32.0+cpu": "0.32.0",
        "llama.cpp/cpu: installed version: 0.7.0-dev (build 11870, commit 74bca3950)": "0.7.0",
        "installed pin 3c75be02f450": "pin 3c75be02f450",
        "tensorfold-native 1.1.4": "1.1.4",
    }
    rejected = {
        "installed 0.00.000.272 I srv  llama_server: initializing ...": "",
        "installed 0.0.0": "",
        "": "",
        "installed": "",
    }

    # When  each line is read for a version
    # Then  only the real version shapes are accepted, and the token that proves it is returned
    for line, want in accepted.items():
        assert ei.version_proof(line) == want, (line, ei.version_proof(line))
    for line, want in rejected.items():
        assert ei.version_proof(line) == want, (line, ei.version_proof(line))


def test_the_log_stamp_and_the_placeholder_are_named_in_the_rule():
    """The two measured false positives are rejected BY NAME, so a new spelling cannot sneak past."""

    # Given the exact strings the old `\\d+\\.\\d+` search accepted
    log_stamp = "installed 0.00.000.406 I srv  llama_server: initializing ..."
    placeholder = "installed 0.0.0"

    # Then  both are refused, and neither is mistaken for a pin
    assert ei.version_proof(log_stamp) == ""
    assert ei.version_proof(placeholder) == ""


# --- the flag half ----------------------------------------------------------------------------------

def test_a_device_policy_cell_that_answers_nothing_is_red_unless_it_is_listed():
    """`probe: device` alone is not an exemption any more (issue #625)."""

    # Given every documented flag failing on a cell that is NOT on the exemption list
    documented = ["--version", "--help"]
    failed = _verdicts(**{"--version": 1, "--help": 1, "-h": 1, "-V": 1})

    # When  the verdict is taken for an unlisted cell
    verdict = ei.decide(documented, failed, "device", engine="sglang", variant="cuda")

    # Then  it is red, and the message says what to do about it
    assert verdict["ok"] is False, verdict
    assert any("DEVICE_ONLY" in f and "#625" in f for f in verdict["failures"]), verdict["failures"]


def test_a_listed_cell_is_exempt_but_says_why():
    """The four measured cells pass, and the log carries the exempting reason."""

    # Given the same all-failing probes on a cell that IS listed
    failed = _verdicts(**{"--version": 1, "--help": 1, "-h": 1, "-V": 1})
    engine, variant = "vllm", "cuda"
    assert (engine, variant) in ei.DEVICE_ONLY, "the measured cell must be on the exemption list"

    # When  the verdict is taken
    verdict = ei.decide(["--version", "--help"], failed, "device", engine=engine, variant=variant)

    # Then  it passes and the note quotes the reason instead of a generic "needs its device"
    assert verdict["ok"] is True, verdict
    assert "#625" in verdict["note"], verdict["note"]


def test_the_exemption_never_applies_to_a_flags_policy_cell():
    """An engine that declares `probe: flags` must answer a flag, listed or not."""

    # Given a listed cell, but the manifest says the flags policy
    failed = _verdicts(**{"--help": 1, "-h": 1})

    # When  the verdict is taken with policy=flags
    verdict = ei.decide(["--help"], failed, "flags", engine="vllm", variant="cuda")

    # Then  the exemption does not rescue it
    assert verdict["ok"] is False, verdict


def test_the_exemption_list_is_exactly_the_measured_cells():
    """Adding a cell to DEVICE_ONLY is a reviewed decision: the list is pinned, with a reason each."""

    # Given the exemption list as committed
    # Then  it is the four cells run 40204145334 measured, each with a reasoned, issue-tagged string
    assert set(ei.DEVICE_ONLY) == {("vllm", "cuda"), ("vllm", "rocm"),
                                   ("tensorrt-llm", "cuda"), ("mlx", "cuda")}, sorted(ei.DEVICE_ONLY)
    for cell, reason in ei.DEVICE_ONLY.items():
        assert "#625" in reason and len(reason) > 30, (cell, reason)


# --- the two broken detections this change fixes -----------------------------------------------------

def test_the_two_broken_detects_no_longer_produce_a_false_version():
    """`sglang` reports the installed distribution; the laurentzuijdwijk fork reports its pin."""

    # Given the committed params for both engines
    sglang = json.loads((REPO / "containers" / "engines" / "params" / "sglang.json").read_text())
    laurent = json.loads((REPO / "containers" / "engines" / "params"
                          / "llama.cpp-laurentzuijdwijk.json").read_text())

    # When  their detect commands are read
    # Then  sglang no longer trusts `sglang.__version__` (0.0.0 in the rocm wheel) …
    for variant, spec in sglang["variants"].items():
        assert "importlib.metadata" in spec["detect"], (variant, spec["detect"])
        assert "sglang.__version__" not in spec["detect"], (variant, spec["detect"])

    # And  the fork no longer documents a --version it does not implement, and proves its pin instead
    binaries = json.loads((REPO / "containers" / "engines" / "binaries.json").read_text())
    laurent_binaries = binaries["engines"]["llama.cpp-laurentzuijdwijk"]
    for variant, entry in laurent_binaries.items():
        assert entry["flags"] == ["--help"], (variant, entry)
    for variant, spec in laurent["variants"].items():
        assert spec["detect"].startswith("echo \"pin "), (variant, spec["detect"])
        assert ei.version_proof(f"installed pin {spec['detect'].split()[-1].strip(chr(34))}")
