"""Real trending-model quant catalog (issue #122): the committed HF class table of
every trending model's real quantized plans and their real downloadable Hugging Face
links — data/trending-quant-catalog.json (the canonical file llgenie's pick logic
reads) and its test fixture tests/fixtures/trending-quant-catalog.json, generated from
data/models.json + the live Hub by scripts/gen_trending_quant_catalog.py
(make sync-quant-catalog). The generator is separate tooling, not llgenie runtime
logic, and makes no LLM calls.

Unit assertions (hermetic except a bounded HTTP-200 probe): the catalog is well-formed,
every model is a real registry model, every engine is a real engine with an image, and
every URL is a concrete, resolvable `https://huggingface.co/<repo>/resolve/<rev>/<file>`
download link. It never downloads a model — it only checks that links exist.

Regression guard: the committed fixture must EXACTLY match the canonical data/ table,
so a sync that changes a link or drops a section is caught here, not silently shipped.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(REPO / "scripts"))
import hub_probe  # noqa: E402  (the one live-Hub link probe, issue #256)
import model_engine_pick as mp  # noqa: E402

CATALOG = REPO / "data" / "trending-quant-catalog.json"       # canonical (llgenie reads this)
FIXTURE = REPO / "tests" / "fixtures" / "trending-quant-catalog.json"  # committed regression copy
REGISTRY = REPO / "data" / "models.json"

_PLAN = {"repo", "revision", "path", "files", "size_gb", "url"}
_DIR_PLAN = _PLAN | {"dir"}
_RESOLVE = re.compile(r"^https://huggingface\.co/[^/]+/[^/]+/resolve/[^/]+/.+$")


def catalog():
    return json.loads(CATALOG.read_text())


def test_fixture_exactly_matches_the_canonical_catalog():
    # Given the canonical data/ table and its committed test fixture
    # When they are compared byte-for-byte
    # Then they are identical — a changed link or a dropped section in the fixture
    #   (regression vs the committed table) fails this test
    assert CATALOG.exists() and FIXTURE.exists()
    assert CATALOG.read_text() == FIXTURE.read_text(), (
        "tests/fixtures/trending-quant-catalog.json differs from data/trending-quant-"
        "catalog.json — run make sync-quant-catalog (a link change or dropped section "
        "must be reviewed and committed) and re-commit both")


def test_catalog_is_well_formed():
    # Given the committed catalog (the HF class table)
    d = catalog()
    # Then it has meta + a files map of model -> engine -> {arch, quants}
    assert set(d) == {"meta", "files"}
    assert d["meta"]["generated_utc"]
    assert d["files"], "catalog is empty"
    for mid, engines in d["files"].items():
        assert mid and isinstance(engines, dict) and engines
        for eng, cell in engines.items():
            assert eng and isinstance(cell, dict)
            assert set(cell) == {"arch", "quants"} and cell["arch"], cell
            assert cell["quants"]
            for it in cell["quants"]:
                # a single-file plan OR a whole-repo snapshot (dir, path="")
                assert set(it) in (_PLAN, _DIR_PLAN), it
                assert it["repo"] and it["files"]
                assert it["files"], it
                if it.get("dir"):
                    assert it["path"] == "" and set(it) == _DIR_PLAN, it
                else:
                    assert it["path"] and it["path"] in it["files"], it


def test_every_model_and_engine_is_real():
    # Given the real registry + real engine image set
    reg = {m["id"]: m for m in mp.load_registry(str(REGISTRY))["models"]}
    ids = mp.engine_ids()
    d = catalog()
    # Then every catalog model exists in the registry, every engine has an image, and its
    # listed archs are a subset of the engine's real image variants (issue #98 / #103)
    for mid, engines in d["files"].items():
        assert mid in reg, f"{mid} not in data/models.json"
        for eng, cell in engines.items():
            assert eng in ids, f"{eng} has no engine image"
            assert set(cell["arch"]) <= set(ids[eng]["variants"]), \
                f"{eng} lists archs {cell['arch']} not among its image variants {ids[eng]['variants']}"
    # and the catalog is a subset of the registry models (nothing invented)
    assert set(d["files"]) <= set(reg)


def test_every_url_is_a_concrete_resolvable_download_link():
    # Given every plan in the catalog
    def _quants():
        for engines in catalog()["files"].values():
            for cell in engines.values():
                yield from cell["quants"]
    urls = [it["url"] for it in _quants()]
    assert urls
    # Then every one is a concrete https://huggingface.co/<repo>/resolve/<rev>/<file> link
    for u in urls:
        assert _RESOLVE.match(u), u
        assert "/resolve/" in u and not u.endswith("/resolve/")
    # and the load path is consistent with the URL (repo + revision + path)
    for it in _quants():
        assert it["repo"] in it["url"], (it["repo"], it["url"])
        if it.get("dir"):
            assert it["url"].endswith(it["files"][0]), (it, it["url"])
        else:
            assert it["path"] != "." and it["path"] in it["url"], it


def test_bounded_sample_of_real_links_exist_http_200():
    """A bounded sample of the catalog's links must exist on the live Hub (no model
    download — a 1-byte ranged probe). This guards that the committed table points at
    real files, not fabricated ones; the full pick-matrix suite probes every offered
    quant of the real run."""
    # one link per (model, engine) — bounded, still representative
    sample = []
    for engines in catalog()["files"].values():
        for cell in engines.values():
            if cell["quants"]:
                sample.append(cell["quants"][0]["url"])
    assert sample
    ok, missing = 0, 0
    for u in sample:
        hit = hub_probe.probe(u)
        if hit.exists:
            ok += 1
        else:
            missing += 1
            print(f"  missing: {u} — {hit.detail}")
    assert ok >= len(sample) * 0.9, f"{missing}/{len(sample)} of the sample links did not answer HTTP 200"


def test_every_engine_and_arch_that_llgenie_offers_is_catalogued():
    # Given every (model, engine) that llgenie would actually recommend on some arch
    reg = mp.load_registry(str(REGISTRY))["models"]
    d = catalog()
    for m in reg:
        engines = mp.rank_engines(m)
        for eng in engines:
            cell = mp.catalog_engine_cell(m["id"], eng["engine"])
            assert cell is not None, \
                f"{m['id']}/{eng['engine']}: llgenie offers an engine that has no catalog entry"
            assert eng["variant"] in cell["arch"], \
                f"{m['id']}/{eng['engine']} offered on {eng['variant']} but the catalog arch " \
                f"list {cell['arch']} excludes it"


def test_every_registry_model_has_a_catalog_entry_or_a_documented_skip():
    # Given a model that llgenie CAN serve on some architecture
    reg = mp.load_registry(str(REGISTRY))["models"]
    d = catalog()
    names = [m["id"] for m in reg if mp.recommend({"models": [m]})]
    for mid in names:
        assert mid in d["files"], f"{mid}: no catalog entry for a servable model"



# ----------------------------------------------------------- the drift guard (`--check`)
# `make check-quant-catalog` regenerates from the LIVE Hub: `mlx_repos()`/`tensorfold_repos()`
# SEARCH huggingface.co, so upstream publishing a new conversion makes a fresh generation
# larger than the committed table with no llgenie change at all. Measured 2026-10-27: four new
# MLX repos turned the gate red on `main` itself, blocking every PR for a reason no PR caused.
# The rule under test is `compare()`'s: a row the committed table HAS must regenerate
# identically (failure), a row the Hub ADDS is a note the next sync records.
import gen_trending_quant_catalog as gen  # noqa: E402

_PLAN_ONE = {"repo": "org/m1-gguf", "revision": "main", "path": "m1-Q4.gguf",
             "files": ["m1-Q4.gguf"], "size_gb": 4.0,
             "url": "https://huggingface.co/org/m1-gguf/resolve/main/m1-Q4.gguf"}
_NEW_PLAN = {"repo": "org/m1-gguf-MLX-4bit", "revision": "main", "path": "",
             "files": ["config.json", "model.safetensors"], "size_gb": 2.0, "dir": True,
             "url": "https://huggingface.co/org/m1-gguf-MLX-4bit/resolve/main/config.json"}


def _committed() -> dict:
    return {"meta": {"generated_utc": "2026-10-13T14:31:40Z"},
            "files": {"m1": {"llama.cpp": {"arch": ["cuda", "cpu"],
                                           "quants": [dict(_PLAN_ONE)]}}}}


def test_an_unchanged_regeneration_is_clean():
    # Given a committed table and the same table regenerated

    # When  the two are compared
    failures, notes = gen.compare(_committed(), json.loads(json.dumps(_committed())))

    # Then  nothing fails and nothing is noted
    assert failures == [] and notes == []


def test_a_repo_upstream_publishes_since_the_sync_is_a_note_not_a_failure():
    # Given a fresh generation that also holds a plan the committed table does not
    fresh = json.loads(json.dumps(_committed()))
    fresh["files"]["m1"]["MLX"] = {"arch": ["metal", "cuda"], "quants": [dict(_NEW_PLAN)]}

    # When  it is compared with the committed table
    failures, notes = gen.compare(_committed(), fresh)

    # Then  the addition is reported and never fails the gate
    assert failures == [], failures
    assert any("MLX" in n for n in notes), notes


def test_a_plan_the_committed_table_has_and_the_generator_lost_still_fails():
    # Given a fresh generation that lost the plan the committed table records
    fresh = json.loads(json.dumps(_committed()))
    fresh["files"]["m1"]["llama.cpp"]["quants"] = []

    # When  it is compared with the committed table
    failures, _notes = gen.compare(_committed(), fresh)

    # Then  the missing plan fails, naming it
    assert any("no longer generated" in f for f in failures), failures


def test_a_changed_plan_still_fails():
    # Given a fresh generation whose plan points at a different file
    fresh = json.loads(json.dumps(_committed()))
    fresh["files"]["m1"]["llama.cpp"]["quants"][0]["path"] = "m1-Q8.gguf"
    fresh["files"]["m1"]["llama.cpp"]["quants"][0]["url"] = \
        "https://huggingface.co/org/m1-gguf/resolve/main/m1-Q8.gguf"

    # When  it is compared with the committed table
    failures, _notes = gen.compare(_committed(), fresh)

    # Then  a silent change to what llgenie would download fails
    assert any("no longer generated" in f for f in failures), failures


def test_a_catalog_rendered_for_another_registry_still_fails():
    # Given a fresh generation under a newer registry
    fresh = json.loads(json.dumps(_committed()))
    fresh["meta"]["generated_utc"] = "2026-10-27T00:00:00Z"

    # When  it is compared with the committed table
    failures, _notes = gen.compare(_committed(), fresh)

    # Then  the registry the catalog was rendered for is asserted
    assert any("make sync-quant-catalog" in f for f in failures), failures


def test_a_reordered_regeneration_is_a_note_not_a_failure():
    # Given a committed table with two plans, regenerated as the SAME two in another order
    # (`mlx_repos()` ranks the Hub search by downloads, and those move)
    second = {"repo": "org/m1-gguf-MLX-8bit", "revision": "main", "path": "",
              "files": ["config.json", "model.safetensors"], "size_gb": 8.0, "dir": True,
              "url": "https://huggingface.co/org/m1-gguf-MLX-8bit/resolve/main/config.json"}
    committed = _committed()
    committed["files"]["m1"]["llama.cpp"]["quants"] = [dict(_PLAN_ONE), dict(second)]
    fresh = json.loads(json.dumps(committed))
    fresh["files"]["m1"]["llama.cpp"]["quants"] = [dict(second), dict(_PLAN_ONE)]

    # When  it is compared with the committed table
    failures, notes = gen.compare(committed, fresh)

    # Then  the reorder is reported rather than failing the gate on data upstream owns
    assert failures == [], failures
    assert any("different order" in n for n in notes), notes
