"""A host agent's behaviour in the tree must be complete, loadable and honest — and the live profile
must follow the tree, not the other way round (issue #791).

Both directions are tested on fixture trees, so nothing here reads the real `~/.hermes/profiles/`:
`check_agent_profiles.check()` is the gate (`make check-agent-profiles`, wired into `ci-unit`) and
`agent_profile_sync.sync()` is the source-of-truth copy (`make sync-agent-profile`).

One case per rejection, because each is a different way the audit trail rots: a listed profile with no
directory, a SOUL that lost the never-merge rule, a skill whose frontmatter name disagrees with its
directory (Hermes loads by name), and a profile that carries a secret-shaped value.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import agent_profile_sync as sync_mod  # noqa: E402
import check_agent_profiles as cap  # noqa: E402

SOUL_OK = """# Agent

**Role:** something

## Standing rules

**Never merge, never push to `main`.** Every merge needs the owner's approval.
"""


def _tree(tmp_path: Path, profiles: dict[str, str | None],
          skills: dict[str, dict[str, str]] | None = None) -> Path:
    """A checkout with `agents/manifest.json` + one SOUL.md per profile + optional skills."""
    root = tmp_path / "repo"
    (root / "agents").mkdir(parents=True)
    (root / "agents" / "manifest.json").write_text(json.dumps({"profiles": list(profiles)}))
    for name, soul in profiles.items():
        (root / "agents" / name).mkdir(parents=True, exist_ok=True)
        if soul is not None:
            (root / "agents" / name / "SOUL.md").write_text(soul)
    for profile, skill_map in (skills or {}).items():
        for skill, text in skill_map.items():
            d = root / "agents" / profile / "skills" / skill
            d.mkdir(parents=True, exist_ok=True)
            (d / "SKILL.md").write_text(text)
    return root


def test_a_listed_profile_with_no_directory_fails(tmp_path):
    root = _tree(tmp_path, {"ghost": None})
    shutil.rmtree(root / "agents" / "ghost", ignore_errors=True)

    problems = cap.check(root)

    assert any("agents/ghost/ does not exist" in p for p in problems), problems


def test_a_profile_without_a_soul_fails(tmp_path):
    root = _tree(tmp_path, {"p1": None})

    problems = cap.check(root)

    assert any("SOUL.md is missing" in p for p in problems), problems


def test_a_soul_that_drops_the_never_merge_rule_fails(tmp_path):
    root = _tree(tmp_path, {"p1": "# Agent\n\nBe helpful.\n"})

    problems = cap.check(root)

    assert any("no longer states the never-merge rule" in p for p in problems), problems


def test_a_skill_whose_name_disagrees_with_its_directory_fails(tmp_path):
    root = _tree(tmp_path, {"p1": SOUL_OK},
                 {"p1": {"right-name": "---\nname: other-name\n---\n\nbody\n"}})

    problems = cap.check(root)

    assert any("declares name: 'other-name'" in p and "does not match its directory" in p for p in problems), problems


def test_a_profile_carrying_a_secret_shaped_value_fails(tmp_path):
    root = _tree(tmp_path, {"p1": SOUL_OK},
                 {"p1": {"leaky": "---\nname: leaky\n---\n\nexport HF_TOKEN=hf_" + "a" * 32 + "\n"}})

    problems = cap.check(root)

    assert any("secret-shaped value" in p for p in problems), problems


def test_the_repositorys_own_profiles_pass_this_gate():
    # The tree this branch ships must satisfy its own gate — a convention the repo violates is not one.
    assert cap.check(REPO) == []
    rows = cap.manifest(REPO)
    assert {row["name"] for row in rows} == {"llgenie-planner", "llgenie-issse-implementer"}
    assert any("llgenie-planner" in line and "SOUL.md yes" in line for line in cap.report(REPO))


def test_sync_writes_the_tree_into_the_live_profile_and_check_then_agrees(tmp_path):
    root = _tree(tmp_path, {"p1": SOUL_OK})
    home = tmp_path / "profiles"

    assert sync_mod.sync("p1", root=root, home=home) == 0
    assert (home / "p1" / "SOUL.md").read_text() == SOUL_OK
    assert sync_mod.sync("p1", root=root, home=home, check=True) == 0


def test_check_names_the_first_drift_and_a_live_only_file_is_never_deleted(tmp_path):
    root = _tree(tmp_path, {"p1": SOUL_OK})
    home = tmp_path / "profiles"
    sync_mod.sync("p1", root=root, home=home)
    # A live-only file (memory-adjacent state, a vendored skill) must survive a sync untouched
    (home / "p1" / "extra.txt").write_text("live only\n")
    (home / "p1" / "SOUL.md").write_text("edited on the host\n")

    assert sync_mod.sync("p1", root=root, home=home, check=True) == 1
    assert sync_mod.sync("p1", root=root, home=home) == 0
    assert (home / "p1" / "SOUL.md").read_text() == SOUL_OK
    assert (home / "p1" / "extra.txt").read_text() == "live only\n"


def test_an_unknown_profile_is_exit_2_not_a_silent_pass(tmp_path, capsys):
    root = _tree(tmp_path, {"p1": SOUL_OK})

    rc = sync_mod.sync("nope", root=root, home=tmp_path / "profiles")

    assert rc == 2
    assert "is not in agents/manifest.json" in capsys.readouterr().err


def test_both_make_targets_exist_with_help_lines_and_are_phony():
    mk = (REPO / "Makefile").read_text()
    for target in ("sync-agent-profile", "check-agent-profiles", "agent-profiles-report"):
        assert f"\n{target}: ##" in mk, target
        assert target in mk.split(".PHONY:", 1)[1].split("\n\n", 1)[0], target
    # And the gate is reached by CI, not only by a human
    ci_unit = mk.split("\nci-unit:", 1)[1].split("\n\n", 1)[0]
    assert "$(MAKE) check-agent-profiles" in ci_unit, ci_unit
