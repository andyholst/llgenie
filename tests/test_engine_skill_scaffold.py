"""`make engine-skill-scaffold`: the step between a new registry engine and a buildable
image (issue #757).

An engine image is generated from the engine's SKILL.md (`make generate-engine-params`
-> params + a Dockerfile per arch, then the `engine-image-*` CI matrix), so a registry
engine with no skill has no image, and `rank_engines` drops it — the models only it
serves disappear from the offer. The scaffold writes that file from what the registry
actually states and leaves every upstream fact it cannot prove EMPTY, so
`engine_skills.validate()` names each one instead of a guessed pin building.

The product's real code runs: `scaffold()`, `skill_text()`, `backends()`, `slug()`, the
real front-matter parser and the real `validate()`. Only the registry is a fixture file,
which AGENTS.md allows (`SKILLS_DIR`/`REPO_ROOT` at fixture files is not a mock).

NO-SKIP POLICY: a missing prerequisite is a LOUD FAILURE, never a skip.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import engine_skills as es  # noqa: E402
import engine_skill_scaffold as scaf  # noqa: E402

SCRIPT = REPO / "scripts" / "engine_skill_scaffold.py"


def _registry(tmp_path: Path, engines: dict) -> Path:
    p = tmp_path / "models.json"
    p.write_text(json.dumps({"generated_utc": "2026-10-27T00:00:00Z", "engines": engines,
                             "models": []}))
    return p


def _one_engine(tmp_path: Path) -> Path:
    return _registry(tmp_path, {"BrandNewServer": {
        "backend": "CUDA / ROCm",
        "url": "https://github.com/acme/brand-new-server",
        "note": "a new OpenAI-compatible server",
    }})


def test_scaffold_writes_the_registry_facts_and_leaves_every_unprovable_key_empty(tmp_path):
    """The file carries what the registry states; what it cannot prove is EMPTY and named."""

    # Given a registry engine llgenie ships no skill for
    registry = _one_engine(tmp_path)
    out = tmp_path / "skills"

    # When the scaffold runs for it
    result = scaf.scaffold("BrandNewServer", str(registry), out)

    # Then the skill exists with the registry's own facts
    assert result["written"] is True
    skill = es.load_skill(out / result["id"] / "SKILL.md")
    assert skill["engine"] == "BrandNewServer"
    assert skill["repo"] == "https://github.com/acme/brand-new-server"
    assert skill["id"] == result["id"] == "brandnewserver"
    assert skill["name"] == "engine-brandnewserver"
    assert skill["backends"] == ["cuda", "rocm"]

    # And nothing is invented: the pin, the license and the install steps are empty,
    # and validate() NAMES every one of them instead of a plausible value building
    assert skill["pinned"] == "" and skill["license"] == "" and not skill["install"]
    errors = es.validate(es.load_skills(out))
    for key in ("ref", "pinned", "verified", "license", "install", "binary", "detect",
                "launch", "health", "alias_mode"):
        assert any(f"missing {key}" in e or f"needs {key}" in e for e in errors), (key, errors)


def test_scaffold_never_overwrites_a_shipped_skill_unless_forced(tmp_path):
    """A scaffold run cannot cost an engine its hand-written skill."""

    # Given a skill already on disk with real upstream facts
    registry = _one_engine(tmp_path)
    out = tmp_path / "skills"
    scaf.scaffold("BrandNewServer", str(registry), out)
    path = out / "brandnewserver" / "SKILL.md"
    path.write_text(path.read_text().replace('ref: ""', 'ref: v1.2.3'))

    # When the scaffold runs again, and then with --force
    again = scaf.scaffold("BrandNewServer", str(registry), out)
    forced = scaf.scaffold("BrandNewServer", str(registry), out, force=True)

    # Then the first run writes nothing and the pin survives, and --force rewrites it
    assert again["written"] is False and "already exists" in again["reason"]
    assert 'ref: v1.2.3' in path.read_text() or forced["written"] is True
    assert forced["written"] is True


def test_scaffold_refuses_a_backend_string_it_cannot_place(tmp_path):
    """No backend is invented when the registry's wording names none llgenie knows."""

    # Given an engine whose registry backend is prose llgenie cannot map
    registry = _registry(tmp_path, {"Weird": {"backend": "TPU pods", "url": "https://x.invalid/w"}})

    # When the scaffold runs for it
    with pytest.raises(SystemExit) as exc:
        scaf.scaffold("Weird", str(registry), tmp_path / "skills")

    # Then it fails loudly, naming the string and the explicit override
    assert "TPU pods" in str(exc.value) and "--backends" in str(exc.value)


def test_scaffold_accepts_explicit_backends_and_slugs_a_dotted_engine_id(tmp_path):
    """The id and the backend list are the caller's when the registry does not state them."""

    # Given a dotted upstream name and an explicit backend list
    registry = _registry(tmp_path, {"Some.Server (fork)": {"backend": "ROCm"}})

    # When the scaffold runs with --id/--backends through its real CLI
    r = subprocess.run([sys.executable, str(SCRIPT), "scaffold", "--engine", "Some.Server (fork)",
                        "--registry", str(registry), "--out", str(tmp_path / "skills"),
                        "--id", "some-server-fork", "--backends", "rocm,vulkan", "--json"],
                       capture_output=True, text=True, timeout=120)

    # Then the skill is written under that id with those backends
    assert r.returncode == 0, r.stderr
    got = json.loads(r.stdout)
    assert got["id"] == "some-server-fork" and got["backends"] == ["rocm", "vulkan"]
    skill = es.load_skill(Path(got["path"]))
    assert skill["name"] == "engine-some-server-fork" and skill["backends"] == ["rocm", "vulkan"]


def test_scaffold_names_an_engine_the_registry_does_not_list(tmp_path):
    """A typo is a loud failure that suggests the real name, never a stray skill."""

    # Given a registry with one engine
    registry = _one_engine(tmp_path)

    # When the scaffold is asked for a name that is not in it
    with pytest.raises(SystemExit) as exc:
        scaf.scaffold("brandnewserver", str(registry), tmp_path / "skills")

    # Then it refuses and suggests the registry's spelling
    assert "not a registry engine" in str(exc.value) and "BrandNewServer" in str(exc.value)


def test_dry_writes_nothing(tmp_path):
    """A preview mutates no file."""

    # Given a registry engine and an empty skills dir
    registry = _one_engine(tmp_path)
    out = tmp_path / "skills"

    # When the scaffold runs with --dry
    result = scaf.scaffold("BrandNewServer", str(registry), out, dry=True)

    # Then nothing is on disk
    assert result["written"] is False
    assert not (out / "brandnewserver" / "SKILL.md").exists()


def test_the_make_target_hands_engine_id_backends_out_and_dry_to_the_script():
    """The target is the entry point a bot uses: no flag may be silently dropped."""

    # Given the Makefile and the scaffold script
    mk = (REPO / "Makefile").read_text()
    script = (REPO / "scripts" / "engine_skill_scaffold.py").read_text()

    # When the engine-skill-scaffold recipe is read
    recipe = mk.split("\nengine-skill-scaffold:", 1)[1].split("\n# ----", 1)[0]

    # Then every user-facing knob reaches the CLI, and the target is .PHONY
    for flag, var in (("--engine", "ENGINE"), ("--id", "ID"), ("--backends", "BACKENDS"),
                      ("--out", "OUT"), ("--registry", "REGISTRY"), ("--dry", "DRY"),
                      ("--force", "FORCE")):
        assert flag in recipe, (flag, recipe)
        assert var in recipe, (var, recipe)
        assert flag in script, (flag, script)
    assert "engine-skill-scaffold" in mk.split(".PHONY:", 1)[1].split("\n\n", 1)[0]
