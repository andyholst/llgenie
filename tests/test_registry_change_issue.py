#!/usr/bin/env python3
"""A changed store opens ONE issue that states what changed (issue #704).

`registry_change_issue.py` compares the committed store/contract/README with the working
tree's and renders the facts. These tests drive the real `compare()`/`render()` over two
real stores built in a temp dir, and the real `open_issue()` with `gh` replaced by a
function that records the command — `gh` is the external system, the script is the product.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import registry_change_issue as RCI  # noqa: E402
import issue_body  # noqa: E402  (the one issue shape, issue #745)


def _store(utc: str, models: list[dict], engines: dict) -> bytes:
    return json.dumps({"generated_utc": utc, "engines": engines, "models": models},
                      indent=2).encode()


def _model(id_: str, name: str, vram: str, formats: list[str]) -> dict:
    return {"id": id_, "name": name, "vram_tier": vram,
            "formats": [{"name": f, "hf": f"a/{id_}-{f.lower()}"} for f in formats],
            "engines": [{"engine": "llama.cpp", "tps": "10"}]}


def _contract(*required: str, backends: list[str] | None = None) -> bytes:
    return json.dumps({
        "type": "object", "required": ["engines", "models"],
        "properties": {
            "engines": {"additionalProperties": {
                "required": ["backend", "note", "url"],
                "properties": {"backend": {"enum": backends or ["CUDA", "Metal", "CPU"]}}}},
            "models": {"items": {"required": list(required),
                                 "properties": {"formats": {"minItems": 1,
                                                            "items": {"required": ["name", "hf"]}}}}},
        },
    }, indent=2).encode()


def _readme(names: list[str]) -> bytes:
    rows = "\n".join(f"| [**{n}**](https://huggingface.co/a/{n}) | **8GB** |" for n in names)
    return f"# Trending\n\n## ❤️ Most loved\n\n| Model | VRAM |\n|---|---|\n{rows}\n\n## Next\n".encode()


def _snapshot(models, engines, required, names, backends=None) -> dict:
    return {
        RCI.STORE: _store("2026-10-26T00:00:00Z", models, engines),
        RCI.CONTRACT: _contract(*required, backends=backends),
        RCI.README: _readme(names),
        RCI.CATALOG: json.dumps({"files": {"m1": {"cuda": {"quants": [{"url": "u1"}]}}}}).encode(),
        RCI.MATRIX: json.dumps({"cases": [{}, {}]}).encode(),
        RCI.GAP: json.dumps({"unresolved": ["NewEngine"]}).encode(),
    }


def test_the_report_names_an_added_model_a_new_engine_and_an_added_contract_key():
    """The three facts an agent needs before it can touch llgenie: a new row, a new engine
    it must decide, and a contract key it does not read yet."""
    # Given  the previous store, and the synced one that added a model, an engine and a key
    prev = _snapshot([_model("m1", "Model One", "16GB", ["GGUF"])],
                     {"llama.cpp": {"backend": "CUDA", "note": "n", "url": "u"}},
                     req_prev := ["id", "name", "vram_tier", "formats", "engines"],
                     ["Model One"])
    cur = _snapshot([_model("m1", "Model One", "16GB", ["GGUF"]),
                     _model("m2", "Model Two", "8GB", ["GGUF", "MLX"])],
                    {"llama.cpp": {"backend": "CUDA", "note": "n", "url": "u"},
                     "NewEngine": {"backend": "Metal", "note": "n", "url": "u"}},
                    req_prev + ["last_seen"], ["Model One", "Model Two"],
                    backends=["CUDA", "Metal", "CPU", "ROCm"])

    # When   the change is compared and rendered
    facts = RCI.compare(prev, cur)
    body = RCI.render(facts)

    # Then   the report names each of them, and says what llgenie must do about it
    assert facts["models_after"] == 2 and facts["engines_after"] == 2
    assert "`m2` — Model Two (VRAM 8GB)" in body
    assert "`NewEngine`" in body
    assert "['last_seen']" in body
    assert "'ROCm'" in body
    assert "#693, #677" in body and "#673/#686" in body
    assert "## Not covered" in body and "#669" in body
    # And the body is the repository's issue shape: the goal first, the diff as `## Technical`
    assert issue_body.missing(body) == [], issue_body.missing(body)
    assert issue_body.headings(body)[-1] == "Technical"
    assert "`m2` — Model Two (VRAM 8GB)" in issue_body.section_body(body, "Technical")


def test_a_second_open_for_the_same_store_updates_instead_of_duplicating(monkeypatch):
    """One issue per store version: the marker is the identity, so a re-run edits it."""
    # Given  gh answering with an open issue that already carries this store's marker
    calls: list[list[str]] = []
    utc = "2026-10-26T00:00:00Z"
    marker = RCI.MARKER.format(utc=utc)

    def fake(args):
        calls.append(args)
        if args[:2] == ["issue", "list"]:
            return json.dumps([{"number": 704, "body": f"old body\n\n{marker}\n"}])
        return "https://github.com/asimov-agent/llgenie/issues/704"

    monkeypatch.setattr(RCI, "run_gh", fake)

    # When   the report is opened for that same store
    result = RCI.open_issue("new body", utc, "asimov-agent/llgenie")

    # Then   it edits issue 704 rather than creating a second one
    assert result == "updated #704"
    assert ["issue", "edit", "704"] == calls[1][:3]
    assert not any(c[:2] == ["issue", "create"] for c in calls)


def test_a_store_with_no_open_issue_creates_exactly_one(monkeypatch):
    """The first sync of a store version files one issue, labelled for the agent."""
    # Given  gh answering with no matching issue
    calls: list[list[str]] = []

    def fake(args):
        calls.append(args)
        if args[:2] == ["issue", "list"]:
            return "[]"
        return "https://github.com/asimov-agent/llgenie/issues/705"

    monkeypatch.setattr(RCI, "run_gh", fake)

    # When   the report is opened
    result = RCI.open_issue("body", "2026-10-27T00:00:00Z", "asimov-agent/llgenie")

    # Then   exactly one issue is created, carrying the agent label
    assert result.endswith("/issues/705")
    creates = [c for c in calls if c[:2] == ["issue", "create"]]
    assert len(creates) == 1
    assert "--label" in creates[0] and RCI.LABEL in creates[0]


def test_dry_run_mutates_nothing(monkeypatch):
    """`DRY=1` previews the decision, it does not touch GitHub."""
    # Given  a marker-less listing
    calls: list[list[str]] = []
    monkeypatch.setattr(RCI, "run_gh", lambda args: calls.append(args) or "[]")

    # When   the open runs dry
    result = RCI.open_issue("body", "2026-10-27T00:00:00Z", "asimov-agent/llgenie", dry=True)

    # Then   it says what it would do and creates nothing
    assert result == "would create one issue"
    assert not any(c[:2] in (["issue", "create"], ["issue", "edit"]) for c in calls)


def test_the_workflow_runs_the_step_even_when_a_gate_is_red():
    """The analysis is most valuable when the store cannot land, so the step must not be
    gated on the check step's success (issue #704)."""
    # Given  the sync workflow, read as text (a strict YAML parse is check-workflows' job)
    import re
    text = (ROOT / ".github" / "workflows" / "registry-sync.yml").read_text()

    # When   the change-issue step is located
    step = re.search(r"- name: State what changed in ONE issue.*?(?=\n      - name: |\Z)", text, re.S)

    # Then   it exists, runs on `always()` when the store changed, and calls the make target
    assert step, "the registry-sync workflow has no change-issue step"
    body = step.group(0)
    assert "always()" in body and "steps.diff.outputs.changed" in body
    assert "make sync-change-issue REPO=" in body
