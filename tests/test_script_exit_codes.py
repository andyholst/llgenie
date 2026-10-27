#!/usr/bin/env python3
"""A `__main__` block must not throw away `main()`'s exit status (issue #701).

`make check-<x>` exists to red a PR. A script whose `main()` returns a status and whose
`__main__` calls `main()` bare exits 0 whatever the status was, so the check prints its
finding and reports success — the gate cannot fail. Measured: `make check-quant-catalog`
printed `FAIL: … is stale` plus a 1000-line diff and exited 0, on `main` @ `3e63bb3`.

This walks `scripts/*.py`. For a module whose `__main__` block calls `main()` without a
`sys.exit(...)` / `raise SystemExit(...)` wrapper, `main()` must not `return` a value.
`scripts/llgenie_serve.py` calls `main()` bare and is fine: its `main()` returns nothing.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


def _main_node(tree: ast.Module) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            return node
    return None


def _returns_a_value(fn: ast.FunctionDef) -> bool:
    """True when any `return` in `main()` carries a value (a status the caller must use)."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and node.value is not None:
            return True
    return False


def _main_block_bare_calls(tree: ast.Module) -> list[int]:
    """Line numbers of `main()` called bare inside the `__main__` guard."""
    lines = []
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        left = getattr(test, "left", None)
        right = getattr(test, "comparators", [None])[0]
        if getattr(left, "id", None) != "__name__" or getattr(right, "value", None) != "__main__":
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
                continue
            func = stmt.value.func
            if isinstance(func, ast.Name) and func.id == "main":
                lines.append(stmt.lineno)
    return lines


def discarded_status(scripts: Path = SCRIPTS) -> list[str]:
    """`path:line` for every script whose `__main__` discards a status `main()` returns."""
    findings = []
    for path in sorted(scripts.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError as e:  # a broken script is another gate's finding
            findings.append(f"{path.name}: cannot parse ({e.msg})")
            continue
        fn = _main_node(tree)
        if fn is None or not _returns_a_value(fn):
            continue
        try:
            shown = path.relative_to(REPO)
        except ValueError:  # a caller's own directory (the guard's own test)
            shown = path.name
        for line in _main_block_bare_calls(tree):
            findings.append(f"{shown}:{line}: __main__ calls main() bare, but main() returns a "
                            f"status that is then discarded")
    return findings


def test_every_main_that_returns_a_status_reaches_the_exit_code():
    """Given every script in scripts/, a bare `main()` in `__main__` must be a main() that
    returns nothing — otherwise the status is lost and the check cannot fail (#701)."""
    # Given  the repository's scripts
    found = discarded_status()

    # Then   no script discards the status main() returns
    assert found == [], "these scripts throw away main()'s exit status:\n  " + "\n  ".join(found)


def test_the_guard_catches_the_defect_it_was_written_for(tmp_path):
    """The guard is proven on a synthetic copy of the shape that shipped: main() returns 1,
    __main__ calls it bare."""
    # Given  a script shaped like the defect
    (tmp_path / "s.py").write_text(
        "def main():\n    return 1\n\n\nif __name__ == '__main__':\n    main()\n")

    # When   the guard runs over that directory
    found = discarded_status(tmp_path)

    # Then   it names the file and the bare call
    assert len(found) == 1
    assert found[0].startswith("s.py:6: ") and "discarded" in found[0]


def test_a_main_that_returns_nothing_is_not_flagged(tmp_path):
    """`llgenie_serve.py`'s shape: main() does the work and returns nothing."""
    # Given  a script whose main() has no return value
    (tmp_path / "s.py").write_text(
        "def main():\n    print('work')\n\n\nif __name__ == '__main__':\n    main()\n")

    # Then   it is not a finding
    assert discarded_status(tmp_path) == []
