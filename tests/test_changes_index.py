"""The change index is one row per file, rendered into CHANGES.md (issue #934)

`CHANGES.md` used to be a single flat table every PR prepended a row to, so every merge re-dirtied
every other open PR and a `DIRTY` PR got no CI run at all (measured 2026-10-29 at `main@97a24063`:
20 of 31 open PRs `DIRTY`). The index is now `docs/changes.d/<note-stem>.md`, one row per file;
`CHANGES.md` is rendered from those fragments by `make changes-index`.

The product is the real code under test (`scripts/changes_index.py`) against real files on disk.

NO-SKIP POLICY: a missing prerequisite is a LOUD FAILURE, never a skip.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import changes_index as ci  # noqa: E402
import unit_tests as ut  # noqa: E402

CLI = REPO / "scripts" / "changes_index.py"


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    """The real CLI, against a real checkout (the repo by default, a scratch tree in tests)."""
    return subprocess.run([sys.executable, str(CLI), *args, "--root", str(root)],
                          capture_output=True, text=True, timeout=120)


def _tree(tmp_path: Path, notes: dict[str, str], rows: dict[str, str]) -> Path:
    """A real checkout skeleton: `agent-wiki/` notes and their `docs/changes.d/` rows."""
    (tmp_path / "agent-wiki").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/changes.d").mkdir(parents=True, exist_ok=True)
    for stem, body in notes.items():
        (tmp_path / "agent-wiki" / f"{stem}.md").write_text(body)
    for stem, row in rows.items():
        (tmp_path / "docs/changes.d" / f"{stem}.md").write_text(row)
    return tmp_path


def _row(date: str, summary: str, stem: str, refs: str) -> str:
    return f"| {date} | {summary} | [{stem}.md](agent-wiki/{stem}.md) | {refs} |\n"


# ---------------------------------------------------------------------------
# the real tree
# ---------------------------------------------------------------------------
def test_the_real_index_accepts_a_committed_changes_md_that_lags_the_fragments():
    """The committed table is the renderer's output — or a lag of it that `report` names (issue
    #1100). A change adds its note and its `docs/changes.d/` row and never edits `CHANGES.md`
    (issue #934 / #1063), so being behind MUST NOT fail the gate; only disagreeing with the
    fragments may."""

    # Given the real checkout
    rendered = ci.render(REPO)
    committed = (REPO / ci.CHANGES).read_text()

    # When the index is rendered and checked
    parsed, errors = ci.rows(REPO)

    # Then every fragment parses, one row stands for every note, and the gate is green
    assert errors == [], errors
    assert len(parsed) == len(list((REPO / "agent-wiki").glob("*.md"))), len(parsed)
    assert ci.check(REPO) == [], ci.check(REPO)
    assert _run(REPO, "check").returncode == 0

    # And the committed table is either current or REPORTED behind — never a silent lag
    state = [l for l in ci.report(REPO).splitlines() if f"{ci.CHANGES}:" in l]
    assert len(state) == 1, state
    assert "current" in state[0] or "row(s) behind" in state[0], state[0]

    # And every row it commits is a row the renderer would write: a stale index may lag, it may
    # never invent. The comparison is a subset, so the fragment tree can keep growing under it.
    committed_rows = [l for l in committed.splitlines() if l.startswith("| 20")]
    rendered_rows = [l for l in rendered.splitlines() if l.startswith("| 20")]
    assert set(committed_rows) <= set(rendered_rows), \
        "CHANGES.md carries a row `make changes-index` would never write"


def test_write_renders_a_lagging_index_and_is_idempotent(tmp_path):
    """`write` is the only author of `CHANGES.md`: a lagging index is not a defect, the write is
    exactly the render, and a second write changes nothing (issues #934, #1100)."""

    # Given two notes with their rows, and a committed CHANGES.md that carries neither
    stems = ("note-2026-10-13", "note-2026-10-14")
    root = _tree(tmp_path, {stem: "# N\n\n#257\n" for stem in stems},
                 {stem: _row(stem[-10:], stem, stem, "#257") for stem in stems})
    (root / ci.CHANGES).write_text("# Changes\n")

    # When the index is checked, then written twice
    lagging = _run(root, "check")
    assert lagging.returncode == 0, lagging.stderr
    assert ci.write(root) == 0
    first = (root / ci.CHANGES).read_text()
    assert ci.write(root) == 0

    # Then the lag was never a defect, the write is the render, and the second write is a no-op
    assert first == ci.render(root)
    assert (root / ci.CHANGES).read_text() == first


def test_the_real_tree_indexes_every_note_with_no_defect():
    """No note is missing a row, no row names a missing note, and the four cells are well-formed."""

    # Given the real checkout
    notes = {p.stem for p in (REPO / "agent-wiki").glob("*.md")}
    rows = {p.stem for p in (REPO / "docs/changes.d").glob("*.md")}

    # When the index is checked
    errors = ci.check(REPO)

    # Then the two sets are the same population and the gate is green
    assert errors == [], errors
    assert notes == rows, (notes - rows, rows - notes)
    assert _run(REPO, "check").returncode == 0


# ---------------------------------------------------------------------------
# the faults the gate exists for
# ---------------------------------------------------------------------------
def test_a_note_without_a_row_is_red_and_adding_its_row_is_green(tmp_path):
    """A change's index row is its own file, and the gate names the one it owes."""

    # Given a note with no row, and one row for a missing note
    root = _tree(tmp_path,
                 {"2026-10-14-change": "# C\n\nIssue #257.\n", "2026-10-14-gone": "# G\n\n#257\n"},
                 {"2026-10-14-gone": _row("2026-10-14", "gone", "2026-10-14-gone", "#257")})

    # When the index is checked
    red = _run(root, "check")

    # Then it is red, naming the unindexed note
    assert red.returncode != 0, red.stdout
    assert "2026-10-14-change.md: is not indexed" in red.stderr, red.stderr

    # And adding that note's own row makes it green
    (root / "docs/changes.d/2026-10-14-change.md").write_text(
        _row("2026-10-14", "change", "2026-10-14-change", "#257"))
    assert ci.check(root) == []
    assert _run(root, "check").returncode == 0


def test_deleting_a_note_reds_the_gate_and_names_it_then_restoring_is_green(tmp_path):
    """The proving test of #934, both directions, through the CLI the gate runs."""

    # Given a complete index (note + its row)
    stem = "2026-10-14-change"
    root = _tree(tmp_path, {stem: "# C\n\nIssue #257.\n"},
                 {stem: _row("2026-10-14", "change", stem, "#257")})
    assert _run(root, "check").returncode == 0

    # When one note is deleted
    (root / "agent-wiki" / f"{stem}.md").unlink()

    # Then the gate is RED and names the note that is gone
    red = _run(root, "check")
    assert red.returncode != 0, red.stdout
    assert f"docs/changes.d/{stem}.md: links agent-wiki/{stem}.md, which does not exist" in red.stderr

    # And restoring it is GREEN
    (root / "agent-wiki" / f"{stem}.md").write_text("# C\n\nIssue #257.\n")
    green = _run(root, "check")
    assert green.returncode == 0, green.stderr
    assert "ok:" in green.stdout


def test_a_row_may_not_index_a_note_of_another_name(tmp_path):
    """One row per change, named for its note: a fragment cannot borrow another change's record."""

    # Given a fragment named for one note that links a different one
    root = _tree(tmp_path, {"2026-10-14-a": "# A\n\n#257\n", "2026-10-14-b": "# B\n\n#257\n"},
                 {"2026-10-14-a": _row("2026-10-14", "a", "2026-10-14-b", "#257"),
                  "2026-10-14-b": _row("2026-10-14", "b", "2026-10-14-b", "#257")})

    # When the index is checked
    errors = ci.check(root)

    # Then the borrowed row is refused, and note `a` is reported unindexed because that row is void
    assert any("must index the note of its own name" in e for e in errors), errors
    assert any("agent-wiki/2026-10-14-a.md: is not indexed" in e for e in errors), errors
    assert not any("2026-10-14-b.md: is not indexed" in e for e in errors), errors


def test_render_orders_rows_newest_first_and_is_stable(tmp_path):
    """The rendered table is newest first, and the same fragments always render the same file."""

    # Given three rows out of order
    stems = ("note-2026-09-01", "note-2026-10-14", "note-2026-10-13")
    dates = {"note-2026-09-01": "2026-09-01", "note-2026-10-14": "2026-10-14",
             "note-2026-10-13": "2026-10-13"}
    root = _tree(tmp_path,
                 {stem: "# N\n\n#257\n" for stem in stems},
                 {stem: _row(dates[stem], stem, stem, "#257") for stem in stems})

    # When it is rendered twice
    first, second = ci.render(root), ci.render(root)

    # Then the newest date comes first and the output is byte-identical
    body = [l for l in first.splitlines() if l.startswith("| 20")]
    assert [l.split("|")[1].strip() for l in body] == ["2026-10-14", "2026-10-13", "2026-09-01"]
    assert first == second


def test_make_changes_index_renders_and_the_gate_runs_it_in_ci():
    """The renderer is a make target, and `check-docs` (which `ci-unit` runs) gates the fragments."""

    # Given the Makefile
    mk = (REPO / "Makefile").read_text()

    # When the check-docs recipe and the phony block are read
    check_docs = mk.split("\ncheck-docs:", 1)[1].split("\ndocs-report:", 1)[0]
    phony = mk.split(".PHONY:", 1)[1].split("\n\n", 1)[0]

    # Then check-docs runs the index check, the render target exists, and both are phony
    assert "python3 scripts/changes_index.py check" in check_docs
    assert "\nchanges-index:" in mk and "\nchanges-index-report:" in mk
    assert "changes-index" in phony and "changes-index-report" in phony

    # And this test file is in the discovered unit suite
    assert "tests/test_changes_index.py" in ut.select(REPO)
