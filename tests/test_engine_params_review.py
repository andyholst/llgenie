"""The engine build-parameter documentation review (issue #583).

`make engine-bump` proves the derived params COMPILE. This leg checks them against the engine's own
documentation for the arch being built, and the deterministic core stays the writer: a proposed `-D`
flag is applied only when its flag AND its quoted evidence both appear in the named upstream file at
the pin. An uncited proposal is dropped and reported, never applied.

These tests run the shipped validation and writer against real files and real document text — no
network, no model: the agent is the external half, and what it may change is decided here.

NO-SKIP POLICY: a missing prerequisite is a LOUD FAILURE, never a skip.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import engine_params_review as epr  # noqa: E402
import engine_skills as es  # noqa: E402

CMAKE_DOC = """
option(GGML_CUDA "compile with CUDA" ON)
option(GGML_CUDA_FA_ALL_VARIANTS "Compile all CUDA flavours" OFF)
# For sm_89 (Ada) the maintainers recommend FA all-variants.
"""

SKILL_TEXT = """---
name: engine-fixture
id: fixture
engine: Fixture
repo: https://example.invalid/fixture
ref: main
pinned: 0
backends: [cuda, rocm]
cmake_flags:
  common: "-DGGML_NATIVE=OFF"
  cuda: "-DGGML_CUDA=ON -DGGML_METAL=OFF"
  rocm: "-DGGML_HIP=ON"
hw_flags: {}
binary_flags: ["--version", "--help"]
---

# Fixture engine
"""

SKILL = {"id": "fixture", "engine": "Fixture", "backends": ["cuda", "rocm"],
         "cmake_flags": {"common": "-DGGML_NATIVE=OFF",
                         "cuda": "-DGGML_CUDA=ON -DGGML_METAL=OFF",
                         "rocm": "-DGGML_HIP=ON"}}


def _proposal(backend="cuda", flag="-DGGML_CUDA_FA_ALL_VARIANTS=ON", doc="CMakeLists.txt",
              quote="option(GGML_CUDA_FA_ALL_VARIANTS", why="the docs ask for it"):
    return (f'PROPOSE {backend} {flag} DOC {doc} "{quote}" WHY {why}')


def _docs(text: str = CMAKE_DOC) -> dict[str, str]:
    return {"CMakeLists.txt": text}


# ---------------------------------------------------------------------------
# the accept path: a documented, arch-specific flag
# ---------------------------------------------------------------------------
def test_a_documented_arch_flag_is_proposed_and_applied(tmp_path):
    """The flag the deterministic derive misses, but the engine's own docs require."""

    # Given a proposal whose flag and quote are both in the upstream CMakeLists at the pin
    proposals = epr.parse_proposals(_proposal())

    # When  it is validated
    accepted, rejected = epr.validate(proposals, _docs(), SKILL)

    # Then  it is accepted, and the writer puts it on the CUDA line of the skill
    assert accepted and not rejected, rejected
    skills_dir = tmp_path / "skills"
    (skills_dir / "fixture").mkdir(parents=True)
    (skills_dir / "fixture" / "SKILL.md").write_text(SKILL_TEXT)
    original = es.SKILLS_DIR
    try:
        es.SKILLS_DIR = skills_dir
        changed = epr.apply_accepted("fixture", accepted)
    finally:
        es.SKILLS_DIR = original
    text = (skills_dir / "fixture" / "SKILL.md").read_text()
    assert changed == ["cuda +-DGGML_CUDA_FA_ALL_VARIANTS=ON"], changed
    assert '-DGGML_CUDA=ON -DGGML_METAL=OFF -DGGML_CUDA_FA_ALL_VARIANTS=ON"' in text, text

    # And   the other backends are untouched
    assert 'rocm: "-DGGML_HIP=ON"' in text, text


def test_a_dry_apply_writes_nothing(tmp_path):
    """A preview must not move the skill."""

    # Given an accepted proposal
    accepted, _ = epr.validate(epr.parse_proposals(_proposal()), _docs(), SKILL)
    skills_dir = tmp_path / "skills"
    (skills_dir / "fixture").mkdir(parents=True)
    target = skills_dir / "fixture" / "SKILL.md"
    target.write_text(SKILL_TEXT)

    # When  it is applied with dry=True
    original = es.SKILLS_DIR
    try:
        es.SKILLS_DIR = skills_dir
        changed = epr.apply_accepted("fixture", accepted, dry=True)
    finally:
        es.SKILLS_DIR = original

    # Then  the change is reported and the file is byte-identical
    assert changed, "a dry run must still report what it would do"
    assert target.read_text() == SKILL_TEXT


# ---------------------------------------------------------------------------
# every way a proposal is refused
# ---------------------------------------------------------------------------
def test_an_undocumented_proposal_is_dropped(tmp_path):
    """A flag the upstream tree does not carry is exactly what this leg exists to refuse."""

    # Given a proposal whose flag appears nowhere in the named file
    proposals = epr.parse_proposals(_proposal(flag="-DMADE_UP_FLAG=ON"))

    # When  it is validated
    accepted, rejected = epr.validate(proposals, _docs(), SKILL)

    # Then  nothing is applied and the drop names the flag and the file
    assert not accepted
    assert any("-DMADE_UP_FLAG" in r and "CMakeLists.txt" in r for r in rejected), rejected


def test_a_quote_that_is_not_in_the_document_is_dropped(tmp_path):
    """A paraphrase is not evidence: the quote is checked by substring."""

    # Given a proposal whose quote the document does not contain
    proposals = epr.parse_proposals(_proposal(quote="the docs say it is nice"))

    # When  it is validated
    accepted, rejected = epr.validate(proposals, _docs(), SKILL)

    # Then  it is dropped for the evidence, not for the flag
    assert not accepted
    assert any("quoted evidence is not in" in r for r in rejected), rejected


def test_a_backend_the_engine_does_not_build_is_rejected(tmp_path):
    """The engine has no vulkan build here: a flag for it is not this repo's parameter."""

    # Given a proposal for a backend outside the skill's backends
    proposals = epr.parse_proposals(_proposal(backend="vulkan"))

    # When  it is validated
    accepted, rejected = epr.validate(proposals, _docs(), SKILL)

    # Then  it is rejected, naming the backends the engine does build
    assert not accepted
    assert any("not one of this engine's backends" in r for r in rejected), rejected


def test_a_flag_already_in_the_params_is_rejected(tmp_path):
    """Nothing to do is a drop with a reason, not a duplicate flag."""

    # Given a proposal for a flag the skill already builds with
    proposals = epr.parse_proposals(_proposal(flag="-DGGML_CUDA=ON"))

    # When  it is validated
    accepted, rejected = epr.validate(proposals, _docs(), SKILL)

    # Then  it is rejected as already present
    assert not accepted
    assert any("already in the params" in r for r in rejected), rejected


# ---------------------------------------------------------------------------
# what the PR carries
# ---------------------------------------------------------------------------
def test_the_section_names_what_was_applied_and_what_was_dropped():
    """The reviewer reads the section, not the step log."""

    # Given one accepted and one refused proposal
    proposals = epr.parse_proposals(_proposal() + "\n" + _proposal(flag="-DNOT_DOCUMENTED=ON"))
    accepted, rejected = epr.validate(proposals, _docs(), SKILL)

    # When  the PR section is built
    text = epr.section("fixture", accepted, rejected)

    # Then  it carries the applied flag with its doc, and the refusal with its reason
    assert "## Documentation review" in text
    assert "-DGGML_CUDA_FA_ALL_VARIANTS=ON" in text and "CMakeLists.txt" in text
    assert "not applied" in text and "-DNOT_DOCUMENTED" in text


def test_a_review_that_proposes_nothing_says_so():
    """Reporting nothing is a correct answer and the PR must be able to say it."""

    # Given no proposals and no refusals
    text = epr.section("fixture", [], [])

    # Then  the section states that the derived params stand as they are
    assert "No documentation-sourced parameter was proposed" in text


# ---------------------------------------------------------------------------
# the wiring: after the bump, before the PR, and never fatal
# ---------------------------------------------------------------------------
def test_the_bump_workflow_runs_the_review_before_the_pr():
    """A review that cannot run must not cost the bump its PR — and must not run after it either."""

    import yaml
    wf = yaml.safe_load((REPO / ".github" / "workflows" / "engine-bump.yml").read_text())
    steps = wf["jobs"]["bump"]["steps"]
    names = [s.get("name") or "" for s in steps]
    review = next((s for s in steps if "Documentation review" in (s.get("name") or "")), None)
    assert review, f"the bump job has no documentation-review step: {names}"

    # Then  it is non-fatal and it runs BEFORE the PR step
    assert review.get("continue-on-error") is True, review
    review_i = steps.index(review)
    pr_i = next(i for i, s in enumerate(steps) if "Open / update the bump PR" in (s.get("name") or ""))
    assert review_i < pr_i, names

    # And   the PR step appends the section the review wrote
    pr = steps[pr_i]["run"]
    assert "params-review-section.md" in pr and "body=" in pr, pr[-600:]

    # And   it calls the three make targets, in order
    run = review["run"]
    for target in ("engine-params-review-brief", "engine-params-review-apply"):
        assert target in run, run
    assert run.index("engine-params-review-brief") < run.index("engine-params-review-apply")


# ---------------------------------------------------------------------------
# the brief is a SELECTION of the tree, not all of it (issue #597)
# ---------------------------------------------------------------------------
def _doc_repo(tmp_path):
    """A real git repo whose tree is dominated by non-build documentation."""
    import subprocess as sp
    repo = tmp_path / "upstream"
    repo.mkdir()
    def git(*args):
        return sp.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
    git("init", "-b", "main", ".")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "T")
    (repo / "CMakeLists.txt").write_text("\n".join(
        f'option(GGML_FLAG_{i} "flag {i}" OFF)' for i in range(1200)))   # > 20 KB, options all the way down
    (repo / "README.md").write_text("build with -DGGML_CUDA=ON and cmake\n" * 400)
    bench = repo / "bench" / "results" / "2026-10-01"
    bench.mkdir(parents=True)
    (bench / "README.md").write_text("benchmark numbers\n" * 2000)
    for i in range(60):
        d = repo / "docs" / f"page{i}"
        d.mkdir(parents=True)
        (d / "README.md").write_text(f"unrelated prose about the project, page {i}\n" * 300)
    git("add", "-A")
    git("commit", "-m", "seed")
    sha = git("rev-parse", "HEAD").stdout.strip()
    return repo, sha


def test_the_brief_selects_by_build_relevance_and_says_what_it_dropped(tmp_path):
    """1.8 MB of bench logs is not a review input: rank, bound the total, and say so (#597)."""

    # Given an upstream tree whose docs are mostly benchmark pages and prose
    repo, sha = _doc_repo(tmp_path)

    # When  the documentation is gathered
    docs, omitted = epr._docs(repo, sha)

    # Then  the CMakeLists that proves the flags is present and NOT cut before its options
    assert "CMakeLists.txt" in docs, sorted(docs)
    assert "option(GGML_FLAG_1199" in docs["CMakeLists.txt"], "the authoritative file was truncated"
    assert len(docs["CMakeLists.txt"]) > epr.DOC_BUDGET, "build evidence is allowed past the per-file cap"

    # And   the brief leaves room for prose: the flag-proving files may not eat the whole budget
    assert sum(len(t) for t in docs.values()) <= epr.DOC_TOTAL_BUDGET
    assert epr.ALWAYS_TOTAL_BUDGET < epr.DOC_TOTAL_BUDGET, "build evidence needs a share, not the lot"

    # And   the benchmark tree is excluded and the total is bounded
    assert not any(p.startswith("bench/") for p in docs), sorted(docs)
    assert sum(len(t) for t in docs.values()) <= epr.DOC_TOTAL_BUDGET
    assert omitted > 0, "the brief must report that it is a selection"


def test_a_build_document_outranks_prose_and_docs_root_is_scanned(tmp_path):
    """A `docs/BUILDING.md` is both FOUND (the glob bug) and ranked above prose (issue #597)."""

    # Given a SMALL tree: one root-level build doc, one sub-level build doc, and many prose pages
    import subprocess as sp
    repo = tmp_path / "small"
    repo.mkdir()

    def git(*args):
        return sp.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)

    git("init", "-b", "main", ".")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "T")
    (repo / "CMakeLists.txt").write_text('option(GGML_CUDA "cuda" OFF)\n')
    (repo / "docs").mkdir()
    (repo / "docs" / "BUILDING.md").write_text(
        "cmake -DGGML_CUDA=ON -DCUDA_ARCHITECTURES=89 build install\n" * 20)
    for i in range(40):
        d = repo / "docs" / f"page{i}"
        d.mkdir()
        (d / "README.md").write_text(f"unrelated prose about the project, page {i}\n" * 200)
    git("add", "-A")
    git("commit", "-m", "seed")
    sha = git("rev-parse", "HEAD").stdout.strip()

    # When  the docs are gathered
    docs, omitted = epr._docs(repo, sha)

    # Then  the docs-root page is FOUND (a `docs/**/*.md`-only glob misses it) and made the cut...
    assert "docs/BUILDING.md" in docs, sorted(docs)

    # And   prose pages were dropped for the budget instead
    assert omitted > 0, "the prose should have been what the budget left out"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
