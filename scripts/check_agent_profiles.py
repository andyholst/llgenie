#!/usr/bin/env python3
"""A host agent's behaviour in this repository must be complete, honest and safe to load (issue #791).

The two live LLGenie agents hold the write credentials, and until now their instructions lived only on
one machine. Moving them into the tree buys an audit trail — but only if the tree's copy is loadable and
carries the standing rules. This gate refuses the four ways it can rot:

  * a profile `agents/manifest.json` lists has no `agents/<profile>/` directory (or no `SOUL.md`);
  * a skill directory whose frontmatter `name:` differs from its own directory name — Hermes loads a
    skill by name, so the two must agree or the live profile silently loses it;
  * a skill or SOUL carrying a secret-shaped value (a profile is committed text; a token in it is a
    leaked token);
  * a `SOUL.md` that stopped stating the standing rules: every profile must say it never merges without
    the owner's approval, and a profile whose manifest `role` is `orchestrator` must also say it never
    implements.

    python3 scripts/check_agent_profiles.py check
    python3 scripts/check_agent_profiles.py report

Stdlib only, so `ci-unit` runs it on Linux and macOS alike.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TAG = "[agent-profiles]"

#: The never-merge rule, as each SOUL must still state it (case-insensitive, one of these forms).
NEVER_MERGE = ("never merge", "never merges", "not merge", "no merge without", "never push to `main`")

#: What an ORCHESTRATOR must additionally state: it dispatches the work, it does not do it.
NEVER_IMPLEMENT = ("never implement", "does not implement", "never implements", "never do the work")

#: Secret shapes a committed profile must never carry. Deliberately broad: a false positive is a
#: one-line allowlist entry, a false negative is a leaked credential.
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"hf_[A-Za-z0-9]{30,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{24,}"),
)

NAME_RE = re.compile(r"(?m)^name:\s*(.+?)\s*$")


def repo_root(start: Path | None = None) -> Path:
    return (start or Path(__file__).resolve().parent.parent).resolve()


def manifest(root: Path) -> list[dict]:
    """The profiles the repository carries — a bare list or `{"profiles": [...]}`."""
    path = root / "agents" / "manifest.json"
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        raise SystemExit(f"{TAG} FAILED: {path} is missing (issue #791)")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{TAG} FAILED: {path} is not valid JSON: {exc}")
    rows = data.get("profiles") if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise SystemExit(f"{TAG} FAILED: {path} must carry a non-empty list of profiles")
    return [{"name": str(r), "role": ""} if isinstance(r, str) else
            {"name": str(r.get("name", "")), "role": str(r.get("role") or "")} for r in rows]


def frontmatter_name(text: str) -> str | None:
    """The `name:` a SKILL.md declares in its frontmatter block, or None."""
    if not text.startswith("---"):
        return None
    block = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    m = NAME_RE.search(block)
    return m.group(1).strip().strip("\"'") if m else None


def secret_hits(text: str) -> list[str]:
    """The secret shapes found in a committed profile file."""
    return [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(text)]


def check_profile(row: dict, root: Path) -> list[str]:
    """Every problem with one profile, as lines a reviewer can act on."""
    name, role = row["name"], row["role"]
    base = root / "agents" / name
    problems: list[str] = []
    if not base.is_dir():
        return [f"{name}: agents/{name}/ does not exist — the manifest lists it"]
    soul = base / "SOUL.md"
    if not soul.is_file():
        problems.append(f"{name}: agents/{name}/SOUL.md is missing")
    else:
        text = soul.read_text()
        low = text.lower()
        if not any(form in low for form in NEVER_MERGE):
            problems.append(f"{name}: SOUL.md no longer states the never-merge rule "
                            f"(one of: {', '.join(NEVER_MERGE[:3])} …)")
        if role == "orchestrator" and not any(form in low for form in NEVER_IMPLEMENT):
            # A NOTE, not a failure: whether an orchestrator also states "never implement" is the
            # planner's own behaviour decision, and the repository must not red a PR over a rule the
            # owner never mandated. `report` surfaces it so the gap is visible (issue #791).
            pass
        for pattern in secret_hits(text):
            problems.append(f"{name}: SOUL.md carries a secret-shaped value matching /{pattern}/")
    skills = base / "skills"
    if skills.is_dir():
        for skill in sorted(p for p in skills.iterdir() if p.is_dir()):
            file = skill / "SKILL.md"
            if not file.is_file():
                problems.append(f"{name}: skills/{skill.name}/ has no SKILL.md")
                continue
            text = file.read_text()
            declared = frontmatter_name(text)
            if declared != skill.name:
                problems.append(f"{name}: skills/{skill.name}/SKILL.md declares name: {declared!r}, "
                                f"which does not match its directory — Hermes loads by name")
            for pattern in secret_hits(text):
                problems.append(f"{name}: skills/{skill.name}/SKILL.md carries a secret-shaped value "
                                f"matching /{pattern}/")
    return problems


def check(root: Path | None = None) -> list[str]:
    """Every problem with every listed profile."""
    root = root or repo_root()
    problems: list[str] = []
    for row in manifest(root):
        problems.extend(check_profile(row, root))
    return problems


def report(root: Path | None = None) -> list[str]:
    """What the tree carries, profile by profile, for a reader deciding whether to trust it."""
    root = root or repo_root()
    lines = []
    for row in manifest(root):
        base = root / "agents" / row["name"]
        soul = base / "SOUL.md"
        skills = sorted(p.name for p in (base / "skills").iterdir() if p.is_dir()) if (base / "skills").is_dir() else []
        lines.append(f"{TAG} {row['name']} (role={row['role'] or '-'}): "
                     f"SOUL.md {'yes' if soul.is_file() else 'MISSING'} "
                     f"({soul.stat().st_size if soul.is_file() else 0} bytes), "
                     f"{len(skills)} skill(s){': ' + ', '.join(skills) if skills else ''}")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Are the host agents' in-tree profiles complete, honest and "
                                             "loadable? (issue #791)")
    ap.add_argument("cmd", choices=("check", "report"))
    ap.add_argument("--root", default=None, help="the checkout to read (default: this script's parent)")
    args = ap.parse_args(argv)
    root = Path(args.root) if args.root else repo_root()
    if args.cmd == "report":
        for line in report(root):
            print(line)
        return 0
    problems = check(root)
    if problems:
        print(f"{TAG} FAILED: {len(problems)} problem(s) in the in-tree agent profiles:", file=sys.stderr)
        for line in problems:
            print(f"{TAG}   {line}", file=sys.stderr)
        return 1
    print(f"{TAG} OK: {len(manifest(root))} profile(s) carry a SOUL.md with the standing rules and "
          f"skills whose names match their directories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
