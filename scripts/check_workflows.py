#!/usr/bin/env python3
"""Every workflow file must be one GitHub will ACCEPT, because a refused file fails silently.

GitHub does not run a workflow file it cannot parse. It creates a run that is `completed`/`failure`
with **zero jobs**, whose `name` is the file PATH rather than the workflow's `name:` — a signal that
reads like a flaky pipeline instead of a broken file, and that no job log exists for
(`gh run view <id> --log-failed` → `log not found`). Nothing in `ci-unit` opened the workflow files,
so a file like this shipped and reddened `main` on every workflow-touching push (issue #330).

The cause that shipped: a `#` line inside a `run: |` block is SCRIPT TEXT, not a YAML comment, so a
literal `${{ ... }}` there is parsed as an expression — and `...` is not an expression, so GitHub
refuses the whole file. PyYAML accepts it (it has no notion of `${{ }}`), which is why review missed
it.

Checks (each is a rule with a name, so a failure says what to do):

    bad-expression     a `${{ … }}` that does not parse: GitHub rejects the WHOLE file for it
    unterminated       a `${{` with no closing `}}` — the same refusal, harder to see
    duplicate-key      the same key twice in one mapping: GitHub refuses it, PyYAML keeps the last
    missing-name       no top-level `name:`: the 0-job run then presents itself as a file path

Commands:
    check_workflows.py check     exit non-zero on any violation (the `ci-unit` gate)
    check_workflows.py report    every workflow file and the checks it passed

Usage:
    python3 scripts/check_workflows.py check
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

#: One `${{ … }}` expression. Non-greedy and DOTALL so a multi-line expression is one match.
EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.S)
#: An opening `${{` that never closes (an unterminated expression is a refusal too).
OPEN_EXPRESSION = re.compile(r"\$\{\{(?![^\n]*\}\})")

#: The tokens GitHub's expression grammar is built from. Everything a real workflow in this repo
#: uses is one of these; anything else (e.g. the `...` of a prose ellipsis) is a refusal.
TOKEN = re.compile(r"""
      \s+
    | (?P<ident>[A-Za-z_][A-Za-z0-9_]*(?:[.\-][A-Za-z0-9_]+)*)
    | (?P<number>-?[0-9]+(?:\.[0-9]+)?)
    | (?P<string>'(?:[^']|'')*'|"(?:[^"\\]|\\.)*")
    | (?P<operator>==|!=|<=|>=|&&|\|\||[()\[\],!<>*+/%-])
""", re.X)


def workflows(root: Path = WORKFLOWS) -> list[Path]:
    """Every workflow file, sorted."""
    return sorted(root.glob("*.yml"))


def bad_expression(expr: str) -> str | None:
    """The first character an expression's grammar does not accept, or None when it parses.

    This is a tokeniser, not a full parser: it accepts the union of forms GitHub documents
    (contexts, `key.path`, indexing, function calls, literals, the operators) and reports the first
    character outside that union. That is exactly the resolution the failure class needs — `...`
    fails on its first `.`, and a mistyped token fails on the character that makes it one.
    """
    pos = 0
    while pos < len(expr):
        m = TOKEN.match(expr, pos)
        if not m:
            return expr[pos]
        pos = m.end()
    return None


class _UniqueKeyLoader(yaml.SafeLoader):
    """A YAML loader that REFUSES a duplicate key, which GitHub also refuses."""


def _no_duplicate_keys(loader: yaml.SafeLoader, node, deep: bool = False) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"found a duplicate key: {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_keys)


def violations(root: Path = WORKFLOWS) -> list[str]:
    """Every way a workflow file is one GitHub would refuse, with the line that does it."""
    bad: list[str] = []
    for path in workflows(root):
        rel = path.relative_to(root.parent.parent).as_posix()
        text = path.read_text()

        for match in EXPRESSION.finditer(text):
            inner = match.group(1)
            offender = bad_expression(inner)
            if offender is not None:
                line = text[:match.start()].count("\n") + 1
                bad.append(f"{rel}:{line}: bad-expression — `${{{{{inner[:40].strip()}…}}}}` does not "
                           f"parse (unexpected {offender!r}); GitHub refuses the WHOLE file for it")

        for match in OPEN_EXPRESSION.finditer(text):
            line = text[:match.start()].count("\n") + 1
            bad.append(f"{rel}:{line}: unterminated — `${{{{` is never closed; GitHub refuses the "
                       f"whole file")

        try:
            data = yaml.load(text, Loader=_UniqueKeyLoader)
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            where = f":{mark.line + 1}" if mark is not None else ""
            bad.append(f"{rel}{where}: duplicate-key — GitHub refuses a file with a duplicate key "
                       f"(PyYAML/our reader silently keep the last): {getattr(exc, 'problem', exc)}")
            continue

        if not isinstance(data, dict) or not data.get("name"):
            bad.append(f"{rel}: missing-name — a workflow with no top-level `name:` presents a "
                       f"0-job run as its file PATH instead of the work it does")

    return bad


def report(root: Path = WORKFLOWS) -> list[dict]:
    """Every workflow file and the checks it passed (for a maintainer reading, not a gate)."""
    rows = []
    for path in workflows(root):
        text = path.read_text()
        try:
            data = yaml.load(text, Loader=_UniqueKeyLoader)
        except yaml.YAMLError:
            data = None
        rows.append({
            "file": path.relative_to(root.parent.parent).as_posix(),
            "expressions": len(EXPRESSION.findall(text)),
            "name": (data or {}).get("name") if isinstance(data, dict) else None,
            "trailing_newline": text.endswith("\n"),
        })
    return rows


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="check_workflows", description=__doc__)
    p.add_argument("cmd", choices=("check", "report"))
    p.add_argument("--root", default=str(WORKFLOWS))
    args = p.parse_args(argv)
    root = Path(args.root)

    if args.cmd == "report":
        rows = report(root)
        print(f"{len(rows)} workflow file(s):")
        for r in rows:
            ok = "." if r["name"] and r["trailing_newline"] else "!"
            print(f"  {ok} {r['file']} — {r['expressions']} expression(s), name={r['name']!r}")
        return 0

    bad = violations(root)
    if bad:
        print(f"[check-workflows] {len(bad)} violation(s):", file=sys.stderr)
        for b in bad:
            print(f"  - {b}", file=sys.stderr)
        return 1
    print(f"[check-workflows] OK: {len(workflows(root))} workflow file(s) parse — no bad "
          f"expression, no duplicate key, every one named")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
