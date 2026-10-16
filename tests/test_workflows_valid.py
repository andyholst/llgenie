"""Every workflow file must be one GitHub will ACCEPT (issue #330).

GitHub refuses a workflow file it cannot parse, and it does so SILENTLY: the push lands a run that is
`completed`/`failure` with **zero jobs**, named after the file PATH rather than the workflow's
`name:`, and `gh run view <id> --log-failed` answers `log not found`. `main` carried one such file
(`.github/workflows/engine-bump-rebase.yml`): a `#` line inside a `run: |` block is script text, and
its literal `${{ ... }}` was parsed as an expression — which `...` is not.

`scripts/check_workflows.py` is the guard; this file is its proof. The real script runs (as a
subprocess for the CLI, imported for the rules) and the real workflow files are read. Nothing here
mocks the thing under test.

NO-SKIP POLICY: a missing prerequisite is a LOUD FAILURE, never a skip.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
WF = REPO / ".github" / "workflows"
sys.path.insert(0, str(REPO / "scripts"))
import check_workflows as cw  # noqa: E402

#: The EXACT text that shipped and was refused (issue #330): the ellipsis is what GitHub's
#: expression parser chokes on, because a `#` line inside `run: |` is script text, not a comment.
SHIPPED_BAD = (
    "jobs:\n"
    "  rebase:\n"
    "    steps:\n"
    "      - run: |\n"
    "          # folded into one `${{ ... }}` so the mode this run took is readable in the log.\n"
    "          echo ok\n"
)

GOOD_RUN = (
    "jobs:\n"
    "  rebase:\n"
    "    steps:\n"
    "      - run: |\n"
    "          if [ \"${{ inputs.dry || 'false' }}\" = \"true\" ]; then echo dry; fi\n"
)


def _tree(tmp_path: Path, name: str, body: str) -> Path:
    root = tmp_path / "repo" / ".github" / "workflows"
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(body)
    return root


def _rules(root: Path) -> list[str]:
    return [v.split(": ", 1)[1].split(" —")[0] for v in cw.violations(root)]


# ---------------------------------------------------------------------------
# the rule: bad-expression
# ---------------------------------------------------------------------------
def test_the_guard_fires_on_the_expression_that_shipped(tmp_path):
    """The negative direction: the exact pre-fix text is a violation, named as bad-expression."""

    # Given the workflow text that shipped on main (issue #330)
    root = _tree(tmp_path, "engine-bump-rebase.yml", "name: x\non:\n  workflow_dispatch:\n" + SHIPPED_BAD)

    # When the guard reads it
    got = _rules(root)

    # Then the unparseable expression is reported, at the line that carries it
    assert got == ["bad-expression"], cw.violations(root)

    # ... and the message points a reviewer at the file, and at the line carrying it
    msg = cw.violations(root)[0]
    assert msg.startswith(".github/workflows/engine-bump-rebase.yml:"), msg
    bad_line = next(n for n, line in enumerate(("name: x\non:\n  workflow_dispatch:\n"
                                                + SHIPPED_BAD).splitlines(), 1)
                    if "${{" in line)
    assert f":{bad_line}:" in msg, (bad_line, msg)


def test_a_valid_expression_is_accepted(tmp_path):
    """The positive direction, so the rule is a parser and not a `${{` grep: a real expression in a
    `run:` block — `inputs.dry || 'false'`, the repo's own idiom — passes."""

    # Given a workflow whose run block carries a real GitHub expression
    root = _tree(tmp_path, "ok.yml", "name: ok\non:\n  workflow_dispatch:\n" + GOOD_RUN)

    # When the guard reads it
    # Then it is clean
    assert cw.violations(root) == [], cw.violations(root)


def test_an_unterminated_expression_is_a_violation(tmp_path):
    """A `${{` that never closes is the same refusal, and harder to see than a bad token."""

    # Given a run block with an unclosed expression
    root = _tree(tmp_path, "u.yml",
                 "name: u\non:\n  workflow_dispatch:\n"
                 "jobs:\n  a:\n    steps:\n      - run: |\n          echo ${{ github.ref\n")

    # When the guard reads it
    # Then it reports the unterminated expression
    assert "unterminated" in _rules(root), cw.violations(root)


# ---------------------------------------------------------------------------
# the other two refusals
# ---------------------------------------------------------------------------
def test_a_duplicate_key_is_a_violation(tmp_path):
    """GitHub refuses a duplicate key; PyYAML and our readers silently keep the last."""

    # Given a mapping with the same key twice
    root = _tree(tmp_path, "d.yml", "name: d\non:\n  workflow_dispatch:\n"
                                    "jobs:\n  a:\n    runs-on: ubuntu-latest\n"
                                    "    timeout-minutes: 5\n    timeout-minutes: 10\n")

    # When the guard reads it
    # Then the duplicate is named
    assert "duplicate-key" in _rules(root), cw.violations(root)


def test_a_workflow_without_a_name_is_a_violation(tmp_path):
    """A file with no top-level `name:` presents a 0-job run as a file path, not as work."""

    # Given a workflow with no `name:`
    root = _tree(tmp_path, "n.yml", "on:\n  workflow_dispatch:\njobs:\n  a:\n    runs-on: ubuntu-latest\n")

    # When the guard reads it
    # Then the missing name is named
    assert "missing-name" in _rules(root), cw.violations(root)


# ---------------------------------------------------------------------------
# the guard over THIS repository, and the exit code CI gates on
# ---------------------------------------------------------------------------
def test_this_repository_has_no_refused_workflow_file():
    assert cw.violations(WF) == [], cw.violations(WF)
    assert cw.main(["check"]) == 0


def test_every_workflow_parses_as_strict_yaml_with_no_duplicate_keys():
    """The class behind the class: strict YAML, a top-level name, and a trailing newline."""

    for path in sorted(WF.glob("*.yml")):
        # Given a workflow file in the tree
        text = path.read_text()

        # When it is parsed the way GitHub does (strict, no duplicate keys)
        data = yaml.load(text, Loader=cw._UniqueKeyLoader)

        # Then it is a mapping with a name, and it ends with a newline
        assert isinstance(data, dict), path.name
        assert data.get("name"), f"{path.name} has no top-level name"

        # (PyYAML reads a bare `on` key as the boolean True — either spelling is a trigger.)
        assert "on" in data or True in data, f"{path.name} declares no trigger"
        assert text.endswith("\n"), f"{path.name} does not end with a newline"


def test_the_shipped_file_no_longer_carries_a_literal_expression():
    """The fix itself: the reworded comment is prose, so no `${{ ... }}` is left in the file."""

    # Given the file that was refused
    text = (WF / "engine-bump-rebase.yml").read_text()

    # When it is read
    # Then no `${{ ... }}` (an ellipsis inside an expression) remains anywhere in it
    assert "${{ ... }}" not in text, "the comment still carries a literal expression"


def test_the_guard_is_wired_into_the_repo():
    """A guard no target names runs nowhere: the make target, .PHONY, help, CI job and the test."""

    # Given the Makefile
    mk = (REPO / "Makefile").read_text()

    # When its wiring is read
    # Then the target exists, is phony, is in help, runs in ci-unit, and its test runs in test-unit
    assert "check-workflows:" in mk
    assert "check-workflows" in mk.split(".PHONY:", 1)[1].split("\n\n", 1)[0]
    assert "make check-workflows" in mk.split("\nhelp:", 1)[1]
    ci_unit = mk.split("\nci-unit:", 1)[1].split("\n\n", 1)[0]
    assert "check-workflows" in ci_unit, "ci-unit must run the guard"
    assert "tests/test_workflows_valid.py" in mk.split("\ntest-unit:", 1)[1].split("\n\n", 1)[0]


def test_the_script_runs_as_a_cli_and_reports(tmp_path):
    """The workflow/test contract: `check` exits non-zero on a violation, `report` never does."""

    # Given the real script and a workflow tree carrying the shipped bad text
    script = REPO / "scripts" / "check_workflows.py"
    root = _tree(tmp_path, "bad.yml", "name: bad\non:\n  workflow_dispatch:\n" + SHIPPED_BAD)

    # When the CLI runs over it
    bad = subprocess.run([sys.executable, str(script), "check", "--root", str(root)],
                         capture_output=True, text=True, cwd=REPO)
    good = subprocess.run([sys.executable, str(script), "report", "--root", str(root)],
                          capture_output=True, text=True, cwd=REPO)

    # Then check fails loudly and report exits 0 with a row per file
    assert bad.returncode == 1, bad.stdout + bad.stderr
    assert "bad-expression" in bad.stderr, bad.stderr
    assert good.returncode == 0, good.stdout + good.stderr
    assert "bad.yml" in good.stdout, good.stdout
