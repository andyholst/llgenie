"""`gh` gets a repo SLUG, never the checkout path (issues #343/#434).

`REPO` in the Makefile is the checkout path — recipes mount it (`-v "$(REPO)":/repo`) — so a
`$(if $(REPO),$(REPO),asimov-agent/llgenie)` default could never apply: `gh` received an absolute path
and refused it ("expected the [HOST/]OWNER/REPO format"). `make issue-cleaner-scan`, `make queued-alarm`
and a dozen other documented invocations failed on their own defaults.

`GH_REPO` is the slug: the repo's own when `REPO` is a path, or a `REPO=owner/name` override.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAKEFILE = REPO / "Makefile"


def _expanded(*args: str) -> str:
    """`make -n <target> …` — the recipe as the shell would receive it."""
    r = subprocess.run(["make", "-n", *args], cwd=REPO, capture_output=True, text=True)
    return r.stdout + r.stderr


def test_no_recipe_passes_the_checkout_path_to_gh():
    """Every `--repo` comes from `$(GH_REPO)`; the path form is the defect."""

    # Given the Makefile
    text = MAKEFILE.read_text()

    # When  every gh-calling recipe line is read
    offenders = [line.strip() for line in text.splitlines()
                 if re.search(r'--repo\s+"?\$\(REPO\)', line)]

    # Then  none of them hands `gh` the checkout path
    assert offenders == [], offenders


def test_the_documented_invocations_carry_the_slug():
    """The two targets that failed on their own docs now expand to the slug."""

    # Given the two targets from the issue
    for target in ("issue-cleaner-scan", "queued-alarm"):
        # When  make expands them
        printed = _expanded(target)

        # Then  the gh call carries the slug and never the checkout path
        assert "asimov-agent/llgenie" in printed, (target, printed[-400:])
        assert str(REPO) not in printed, (target, printed[-400:])


def test_an_explicit_repo_override_still_wins():
    """`REPO=owner/name` keeps working: `REPO` is a path only when it looks like one."""

    # Given an operator naming another repository
    # When  the target expands with that override
    printed = _expanded("issue-cleaner-scan", "REPO=trending-local-llms/trending-local-llms")

    # Then  the override reaches gh, not the default
    assert "trending-local-llms/trending-local-llms" in printed, printed[-400:]
    assert "asimov-agent/llgenie" not in printed


def test_the_slug_is_a_slug_by_default():
    """`GH_REPO` is `asimov-agent/llgenie` when `REPO` is the checkout path."""

    # Given the checkout path as REPO
    # When  GH_REPO is printed through a make expression
    out = subprocess.run(["make", "-s", "--eval=print-gh-repo: ; @echo $(GH_REPO)",
                          "print-gh-repo"], cwd=REPO, capture_output=True, text=True).stdout.strip()

    # Then  it is the slug, never a path
    assert out == "asimov-agent/llgenie", out
