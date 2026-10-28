"""`make check-pr-hygiene` refuses a bot PR whose `AGENTS:` citation is unreachable (issue #792).

The rule is ancestry, not equality with the merge base: `rebase-bot` moves the merge base while the
cited rulebook stays reachable from both head and base, so equality would reject exactly the PRs that
were kept current. These tests build real commits, because ancestry is the thing under test.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import check_pr_hygiene as hy  # noqa: E402


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def commit(root: Path, name: str, subject: str) -> str:
    (root / name).write_text(subject)
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", subject)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    commit(root, "a.txt", "base")
    git(root, "checkout", "-q", "-b", "feature")
    commit(root, "b.txt", "work")
    return root


def body(sha: str, size: int = 87255, lines: int = 1302) -> str:
    return f"Closes #792.\n\nAGENTS: {sha} {size}b {lines}l\n\nBody text.\n"


def test_a_cited_rulebook_reachable_from_both_sides_passes(repo: Path):
    base = git(repo, "rev-parse", "main")
    assert hy.agents_line_findings(repo, "feature", base, body(base)) == []


def test_a_citation_that_is_not_an_ancestor_of_the_head_is_refused(repo: Path):
    git(repo, "checkout", "-q", "main")
    elsewhere = commit(repo, "c.txt", "not on the feature branch")
    git(repo, "checkout", "-q", "feature")
    items = hy.agents_line_findings(repo, "feature", "main", body(elsewhere))
    assert [i["key"] for i in items] == ["agents-line"]
    assert "not an ancestor of feature" in items[0]["detail"]


def test_a_citation_the_base_lacks_is_refused(repo: Path):
    head = git(repo, "rev-parse", "feature")
    git(repo, "checkout", "-q", "--detach", "main")
    items = hy.agents_line_findings(repo, "feature", "main", body(head))
    assert items and "not an ancestor of main" in items[0]["detail"]


def test_a_body_with_no_agents_line_is_refused(repo: Path):
    items = hy.agents_line_findings(repo, "feature", "main", "Closes #792.\n\nNo citation here.\n")
    assert items and "run `make bot-preflight`" in items[0]["detail"]


def test_a_sha_that_is_not_a_commit_is_refused(repo: Path):
    items = hy.agents_line_findings(repo, "feature", "main", body("0" * 40))
    assert items and "not a commit in this clone" in items[0]["detail"]


def test_the_cli_exits_non_zero_for_an_unreachable_citation(repo: Path, tmp_path: Path):
    git(repo, "checkout", "-q", "-b", "scratch", "main")     # never commit onto main: it must stay put
    elsewhere = commit(repo, "d.txt", "somewhere else")
    git(repo, "checkout", "-q", "feature")
    f = tmp_path / "body.md"
    f.write_text(body(elsewhere))
    rc = hy.main(["agents-line", "--root", str(repo), "--head", "feature", "--base", "main",
                  "--body-file", str(f)])
    assert rc == 1
    f.write_text(body(git(repo, "rev-parse", "main")))
    assert hy.main(["agents-line", "--root", str(repo), "--head", "feature", "--base", "main",
                    "--body-file", str(f)]) == 0