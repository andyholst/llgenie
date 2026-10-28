"""The bot preflight (issue #792): a leg proves its base is current `main` and it read the rulebook.

Every rule runs against a **real** git pair — a bare repository that plays `origin`, and a clone of
it — with the real `git` doing the fetch, the fast-forward and the divergence check. Nothing is
stubbed: the preflight is a git fact, so a fake remote would prove nothing. The remote is a local
path, which the preflight accepts and says so, because only a GitHub URL whose slug is not
`asimov-agent/llgenie` is a refusal.

NO-SKIP POLICY: a missing prerequisite is a LOUD FAILURE, never a skip. `git` is required.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import bot_preflight as bp  # noqa: E402

#: An AGENTS.md with two rule headings — the fixture's rulebook.
AGENTS = """# Agents

Intro prose that is not a rule.

## Git workflow

Always branch off main.

## Every PR carries the issue

State the problem first.

### A subsection is not a top-level rule

Detail.
"""


def git(cwd: Path, *args: str) -> str:
    """Run real git, with an identity, and return its stdout."""
    proc = subprocess.run(
        ["git", "-c", "user.name=Asimov Agent", "-c", "user.email=support@docondee.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=str(cwd), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {cwd}: {proc.stderr or proc.stdout}")
    return proc.stdout


def clone(tmp_path: Path) -> tuple[Path, Path]:
    """A bare `origin` carrying `main`, and a clone of it — the real pair every test uses."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(origin))
    seed = tmp_path / "seed"
    git(tmp_path, "init", "-b", "main", str(seed))
    (seed / "AGENTS.md").write_text(AGENTS, encoding="utf-8")
    # The record is a run input, exactly as in this repository: without the ignore line the
    # preflight's own file would make the next run see a dirty tree.
    (seed / ".gitignore").write_text("preflight.txt\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-m", "chore: the rulebook")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "-u", "origin", "main")
    work = tmp_path / "work"
    git(tmp_path, "clone", str(origin), str(work))
    return origin, work


def advance_origin(tmp_path: Path, origin: Path) -> str:
    """One more commit on `origin/main`, returning its sha (the clone is now behind)."""
    seed = tmp_path / "seed"
    (seed / "main.py").write_text("print('one more')\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-m", "feat: move main on")
    git(seed, "push", "origin", "main")
    return git(seed, "rev-parse", "HEAD").strip()


def recorded(work: Path) -> dict[str, str]:
    """`preflight.txt` as key -> value."""
    text = (work / bp.PREFLIGHT).read_text(encoding="utf-8")
    return {k: v for k, v in (line.split(": ", 1) for line in text.splitlines() if ": " in line)}


# ---------------------------------------------------------------------------------------------
# a checkout that is exactly main
# ---------------------------------------------------------------------------------------------


def test_a_clean_checkout_at_main_passes_and_records_the_line(tmp_path: Path, capsys):
    """At `main`, the preflight passes and records the line a PR body repeats."""

    # Given a clean clone whose HEAD is already the commit origin/main names
    _, work = clone(tmp_path)
    expected_sha = git(work, "rev-parse", "origin/main").strip()
    size = len(AGENTS.encode())
    lines = AGENTS.count("\n")

    # When  the preflight runs
    rc = bp.main(["--root", str(work), "--profile", "issue-bot-triage"])

    # Then  it exits 0, the tree is at main, and preflight.txt carries the AGENTS line first
    out = capsys.readouterr()
    assert rc == 0, out.err
    text = (work / bp.PREFLIGHT).read_text(encoding="utf-8")
    first = text.splitlines()[0]
    assert first == f"AGENTS: {expected_sha} {size}b {lines}l"
    assert first == bp.agents_line(expected_sha, AGENTS)
    fields = recorded(work)
    assert fields["MAIN"] == expected_sha
    assert fields["PROFILE"] == "issue-bot-triage"
    assert fields["AGENTS-HEADINGS"].startswith("sha256:")
    assert " at " in f" {fields['TREE']} "
    assert bp.parse_agents_line(first) == {"sha": expected_sha, "bytes": str(size), "lines": str(lines)}

    # And `--check` on the file it just wrote passes — a fresh record is not "stale"
    assert bp.main(["--root", str(work), "--check"]) == 0


def test_a_clean_behind_checkout_is_fast_forwarded(tmp_path: Path, capsys):
    """A clean clone that is behind is brought to `main`, never left stale."""

    # Given a clone one commit behind origin/main
    origin, work = clone(tmp_path)
    new_sha = advance_origin(tmp_path, origin)
    assert git(work, "rev-parse", "HEAD").strip() != new_sha

    # When  the preflight runs
    rc = bp.main(["--root", str(work)])

    # Then  it exits 0 and HEAD is origin/main afterwards
    out = capsys.readouterr()
    assert rc == 0, out.err
    assert git(work, "rev-parse", "HEAD").strip() == new_sha
    assert recorded(work)["MAIN"] == new_sha
    assert "fast-forwarded" in recorded(work)["TREE"]


def test_a_branch_ahead_of_main_passes(tmp_path: Path, capsys):
    """A feature branch that already contains main passes — nothing of main is missing."""

    # Given a clone with one commit of its own on top of main
    _, work = clone(tmp_path)
    (work / "feature.txt").write_text("work\n", encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-m", "feat: the branch's own work")
    own = git(work, "rev-parse", "HEAD").strip()

    # When  the preflight runs
    rc = bp.main(["--root", str(work)])

    # Then  it exits 0, HEAD is untouched, and the record says the tree is ahead
    out = capsys.readouterr()
    assert rc == 0, out.err
    assert git(work, "rev-parse", "HEAD").strip() == own
    assert recorded(work)["MAIN"] == git(work, "rev-parse", "origin/main").strip()
    assert "ahead" in recorded(work)["TREE"]


# ---------------------------------------------------------------------------------------------
# refusals — a leg that cannot prove its base does not start
# ---------------------------------------------------------------------------------------------


def test_a_dirty_checkout_refuses_and_names_the_paths(tmp_path: Path, capsys):
    """An uncommitted change stops the preflight before it touches the tree."""

    # Given a clean clone whose tracked file is edited
    origin, work = clone(tmp_path)
    advance_origin(tmp_path, origin)
    (work / "AGENTS.md").write_text(AGENTS + "\nlocal edit\n", encoding="utf-8")

    # When  the preflight runs
    rc = bp.main(["--root", str(work)])

    # Then  it exits 2, names the path, and HEAD has not moved
    out = capsys.readouterr()
    assert rc == 2
    assert "uncommitted changes" in out.err
    assert "AGENTS.md" in out.err
    assert git(work, "rev-parse", "HEAD").strip() == git(work, "rev-parse", "origin/main~1").strip()
    assert not (work / bp.PREFLIGHT).exists()


def test_a_diverged_checkout_refuses_and_prints_the_counts(tmp_path: Path, capsys):
    """A branch that has a commit main lacks cannot fast-forward, so it is refused loudly."""

    # Given a clone with a local commit, while origin/main also moved on
    origin, work = clone(tmp_path)
    (work / "local.txt").write_text("mine\n", encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-m", "feat: local work")
    advance_origin(tmp_path, origin)

    # When  the preflight runs
    rc = bp.main(["--root", str(work)])

    # Then  it exits 2 and prints the left/right counts of HEAD...origin/main
    out = capsys.readouterr()
    assert rc == 2
    assert "diverged" in out.err
    assert "git rev-list --left-right --count" in out.err
    assert "1 (HEAD-only) 1 (main-only)" in out.err
    assert not (work / bp.PREFLIGHT).exists()


def test_an_origin_that_is_not_this_repository_refuses(tmp_path: Path, capsys):
    """A GitHub origin that names another repository is a refusal, before any fetch."""

    # Given a clone whose origin is another repository's GitHub URL
    _, work = clone(tmp_path)
    git(work, "remote", "set-url", "origin", "https://github.com/someone/else.git")

    # When  the preflight runs
    rc = bp.main(["--root", str(work)])

    # Then  it exits 2 and names the slug it read
    out = capsys.readouterr()
    assert rc == 2
    assert bp.REQUIRED_SLUG in out.err
    assert "someone/else" in out.err


def test_an_unreachable_remote_refuses(tmp_path: Path, capsys):
    """A remote that cannot be fetched is a failure — never a silent start on a stale base."""

    # Given a clone whose origin cannot be reached
    _, work = clone(tmp_path)
    git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))

    # When  the preflight runs
    rc = bp.main(["--root", str(work)])

    # Then  it exits 2 and names the fetch failure
    out = capsys.readouterr()
    assert rc == 2
    assert "cannot fetch" in out.err
    assert "refusing to start on a stale base" in out.err


# ---------------------------------------------------------------------------------------------
# what the record is worth: the digest, and a stale file
# ---------------------------------------------------------------------------------------------


def test_the_heading_digest_follows_the_rule_headings_not_the_prose(tmp_path: Path, capsys):
    """The digest moves when a rule heading changes, not when a sentence is reworded."""

    # Given a recorded heading digest for the rulebook
    _, work = clone(tmp_path)
    assert bp.main(["--root", str(work)]) == 0
    before = recorded(work)["AGENTS-HEADINGS"]

    # When  a sentence inside an existing section is reworded, then a new rule heading is added
    reworded = AGENTS.replace("Always branch off main.", "Always branch off main, always.")
    assert bp.agents_record(reworded)[2] == before.split("sha256:")[1]
    new_rule = bp.agents_record(AGENTS + "\n## A brand new rule\n\nText.\n")[2]

    # Then  the reworded text keeps the digest and the new heading changes it
    assert new_rule != before.split("sha256:")[1]


def test_check_mode_names_the_first_difference_against_a_stale_file(tmp_path: Path, capsys):
    """`--check` catches a record made against an older main, before anything is written."""

    # Given a preflight.txt recorded against an older main
    origin, work = clone(tmp_path)
    assert bp.main(["--root", str(work)]) == 0
    old_sha = recorded(work)["MAIN"]
    advance_origin(tmp_path, origin)

    # When  the preflight runs with --check
    rc = bp.main(["--root", str(work), "--check"])

    # Then  it exits 2, names the field and both values, and the file is unchanged
    out = capsys.readouterr()
    assert rc == 2
    assert "stale" in out.err and "AGENTS" in out.err
    assert old_sha in out.err
    assert recorded(work)["MAIN"] == old_sha


def test_preflight_txt_is_gitignored():
    """The record is a run input, so real git must not see it in this repository."""

    # Given the repository's .gitignore
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")

    # When  git asks whether the preflight record is ignored
    proc = subprocess.run(["git", "check-ignore", "-v", bp.PREFLIGHT], cwd=str(REPO),
                          capture_output=True, text=True)

    # Then  it is ignored
    assert bp.PREFLIGHT in ignore
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------------------------
# wiring
# ---------------------------------------------------------------------------------------------


def test_the_make_target_is_phony_documented_and_forwards_the_profile():
    """`make bot-preflight` exists, is phony, carries a help line, is documented, forwards everything."""

    # Given the real Makefile and the bot documentation
    makefile = (REPO / "Makefile").read_text(encoding="utf-8")
    bots = (REPO / "docs" / "BOTS.md").read_text(encoding="utf-8")

    # When  they are read
    recipe = next((line for line in makefile.splitlines() if line.startswith("bot-preflight:")), "")

    # Then  the target, its help line, its .PHONY entry, its docs and its parameters all exist
    assert recipe, "no `bot-preflight:` target in the Makefile"
    assert "## " in recipe
    # `.PHONY:` is declared in several blocks, so every declared target is gathered.
    phony = [line for line in makefile.splitlines()
             if line.startswith(".PHONY:") or (line.startswith("\t") and "bot-preflight" in line)]
    assert any("bot-preflight" in line for line in phony), "bot-preflight is not in a .PHONY: block"
    assert "make bot-preflight" in bots
    assert "scripts/bot_preflight.py" in makefile
    for param in ("PROFILE", "CHECK", "REMOTE", "BRANCH"):
        assert param in recipe, f"{param} is not forwarded by the target"
