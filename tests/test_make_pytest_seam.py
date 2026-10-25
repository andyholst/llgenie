"""Every pytest in a make recipe runs in the test image (or the dev venv) — never on a bare host python.

Issue #621: `make test-published-engine` called `python3 -m pytest tests/test_published_engine_binary.py`
as a HOST command. The GitHub runner has a `python3` and no pytest, so the step could only ever fail with
`/usr/bin/python3: No module named pytest` — and because the published matrix was empty at the time, no run
exercised it until `engine-build` (#616) re-populated the rows. Every other test stage in the repo runs
through one of two seams: `$(TEST_RUN)` (the test image in CI, the venv on a dev host) or
`$(call engine_test,…)` (the test image with the engine's env). This test keeps the next recipe honest.

No product code is involved: the Makefile is the artifact, and the assertion is on its text.
"""
from __future__ import annotations

import re

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAKEFILE = REPO / "Makefile"

#: The seams a test command may run through. `$(TEST_RUN)` and `$(ENGINE_TEST_RUN)` resolve to the test
#: image in CI and to the venv on a dev host; `$(call engine_test,…)` builds the same container command with
#: the engine's env; the literal image name catches a hand-written `docker run … llgenie/test:latest`.
SEAMS = ("$(TEST_RUN)", "$(ENGINE_TEST_RUN)", "$(call engine_test,", "llgenie/test:latest")

#: A target header, e.g. `test-published-engine:` (not a variable assignment, not a `.PHONY` list).
_TARGET = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*):")


def _logical_recipe_lines(text: str) -> list[tuple[str, str]]:
    """(target, the command) for every recipe line, with `\\` continuations joined.

    Comments are skipped — a recipe's `#` line is documentation, and this rule is about commands.
    """
    out: list[tuple[str, str]] = []
    target = ""
    pending = ""
    for raw in text.splitlines():
        if _TARGET.match(raw) and not raw.startswith("\t"):
            target = _TARGET.match(raw).group(1)  # type: ignore[union-attr]
            pending = ""
            continue
        if not raw.startswith("\t"):
            continue
        line = raw.strip()
        if line.startswith("#"):
            continue
        pending = f"{pending} {line}".strip() if pending else line
        if pending.endswith("\\"):
            pending = pending[:-1].strip()
            continue
        out.append((target, pending))
        pending = ""
    if pending:
        out.append((target, pending))
    return out


def test_every_pytest_in_a_make_recipe_runs_through_the_test_seam():
    """A recipe that needs pytest must get it from the test image (or the venv), never from the host."""

    # Given every recipe line in the Makefile, continuations joined
    recipes = _logical_recipe_lines(MAKEFILE.read_text())

    # When  the lines that run pytest are read
    pytest_lines = [(t, c) for t, c in recipes if re.search(r"\bpython3? -m pytest\b", c)]

    # Then  there is more than one (the suite is driven from several targets) …
    assert pytest_lines, "no pytest invocation found in the Makefile: the parser or the targets changed"

    # And  every single one runs through a seam that provides pytest
    offenders = [(t, c) for t, c in pytest_lines if not any(seam in c for seam in SEAMS)]
    assert not offenders, (
        "a make recipe runs pytest on a bare host python (issue #621 — the runner has no pytest):\n"
        + "\n".join(f"  {t}: {c}" for t, c in offenders)
    )

    # And  the target that failed, specifically, is the one that carries the published-image env
    published = [c for t, c in recipes if t == "test-published-engine" and "pytest" in c]
    assert published, "test-published-engine no longer runs its pytest"
    assert any("$(call engine_test," in c and "LLGENIE_PUBLISHED_PULLED=1" in c for c in published), \
        f"test-published-engine must pass its env into the test image, got: {published}"
