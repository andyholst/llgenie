"""The bot preflight (issue #792): fetch, sync, measure, and refuse a stale tree.

Every test builds a real repository with a bare `origin`, because the thing under test *is* git
plumbing — a mocked `merge-base` would pass while the target refused every clean checkout.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import bot_preflight as bp  # noqa: E402

RULEBOOK = """# Rules

## First rule
Body text here.

## Second rule
More body text.

### A sub-rule
Detail.
"""


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def _commit(root: Path, agents: str, subject: str) -> str:
    (root / "AGENTS.md").write_text(agents)
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", subject)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A clone whose `origin/main` is a bare repository — the shape a bot actually works in."""
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare)], check=True)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", str(bare), str(work)], check=True)
    git(work, "checkout", "-q", "-b", "main")
    _commit(work, RULEBOOK, "seed")
    git(work, "push", "-q", "origin", "main")
    git(work, "remote", "set-head", "origin", "main")
    return work


def test_the_record_names_the_main_sha_and_the_rulebooks_measurements(repo: Path):
    record = bp.preflight(repo)
    assert record["main"] == git(repo, "rev-parse", "origin/main")
    assert record["agents_bytes"] == len(RULEBOOK.encode())
    assert record["agents_lines"] == RULEBOOK.count("\n")
    assert record["agents_headings"] == 3          # `## First rule`, `## Second rule`, `### A sub-rule`


def test_the_agents_line_is_the_one_a_pr_body_carries(repo: Path):
    line = bp.agents_line(bp.rulebook(repo))
    sha = git(repo, "rev-parse", "origin/main")
    assert line == f"AGENTS: {sha} {len(RULEBOOK.encode())}b {RULEBOOK.count(chr(10))}l"


def test_editing_prose_keeps_the_heading_digest_but_adding_a_rule_moves_it(repo: Path):
    before = bp.heading_digest(RULEBOOK)
    assert bp.heading_digest(RULEBOOK.replace("Body text here.", "Different prose.")) == before
    assert bp.heading_digest(RULEBOOK + "\n## Third rule\n") != before


def test_a_clean_checkout_behind_main_is_fast_forwarded(repo: Path):
    git(repo, "checkout", "-q", "-b", "leg")
    second = _commit(repo, RULEBOOK.replace("Body text here.", "Moved on."), "advance main")
    git(repo, "push", "-q", "origin", "leg:main")
    git(repo, "checkout", "-q", "leg~0")                     # leg now equals the old main
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    assert git(repo, "rev-parse", "HEAD") != second
    record = bp.preflight(repo)
    assert git(repo, "rev-parse", "HEAD") == second
    assert record["main"] == second


def test_a_dirty_checkout_behind_main_is_refused_with_its_paths(repo: Path):
    _commit(repo, RULEBOOK + "\n## Later\n", "advance main")
    git(repo, "push", "-q", "origin", "HEAD:main")
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "dirty.txt").write_text("uncommitted\n")
    with pytest.raises(bp.PreflightError) as exc:
        bp.preflight(repo)
    assert "dirty" in str(exc.value)
    assert "dirty.txt" in str(exc.value)


def test_a_diverged_checkout_is_refused_and_the_preflight_never_rebases(repo: Path):
    git(repo, "checkout", "-q", "-b", "leg")
    _commit(repo, RULEBOOK + "\n## Main side\n", "main moves")
    git(repo, "push", "-q", "origin", "HEAD:main")
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    mine = _commit(repo, RULEBOOK + "\n## Leg side\n", "leg moves")
    with pytest.raises(bp.PreflightError) as exc:
        bp.preflight(repo)
    message = str(exc.value)
    assert "diverged" in message and "1 commit(s) ahead" in message
    assert git(repo, "rev-parse", "HEAD") == mine, "the leg's own commit must survive a refused preflight"


def test_the_record_the_preflight_writes_does_not_make_the_next_run_refuse(repo: Path):
    """Running it twice in a row must pass: `preflight.txt` is this target's own output, not the leg's dirt."""
    bp.write_record(repo)
    assert (repo / bp.RECORD).exists()
    record = bp.preflight(repo)                      # a second run in the same tree
    assert record["main"] == git(repo, "rev-parse", "origin/main")


def test_check_mode_fails_when_the_record_is_missing_or_stale(repo: Path):
    assert bp.stale_record(repo) is not None
    bp.write_record(repo)
    assert bp.stale_record(repo) is None
    _commit(repo, RULEBOOK + "\n## New rule\n", "rulebook grew")
    git(repo, "push", "-q", "origin", "HEAD:main")
    (repo / "preflight.txt").write_text((repo / "preflight.txt").read_text().replace("87255", "1"))
    assert "stale" in (bp.stale_record(repo) or "")


def test_the_check_cli_exits_non_zero_on_a_stale_record(repo: Path):
    assert bp.main(["--root", str(repo), "--check"]) == 1
    bp.write_record(repo)
    assert bp.main(["--root", str(repo), "--check"]) == 0


def test_a_refused_preflight_exits_non_zero_and_says_why(tmp_path: Path):
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    assert bp.main(["--root", str(plain), "--no-sync"]) == 1
