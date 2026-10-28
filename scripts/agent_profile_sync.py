#!/usr/bin/env python3
"""The repository is the source of truth for a host agent's behaviour (issue #791).

A host agent's `SOUL.md` and its skills used to live only in `~/.hermes/profiles/<profile>/`, outside
version control: nobody could diff what a credential-holding agent was told between two incidents, and a
profile reinstall silently lost the behaviour. This copies the in-tree copy into the live profile and,
with `--check`, proves the two agree.

    python3 scripts/agent_profile_sync.py sync  --profile llgenie-planner
    python3 scripts/agent_profile_sync.py check --profile llgenie-planner

WHAT IT DOES NOT DO, deliberately:

- **it never deletes a live file the repo does not carry.** A profile holds memory-adjacent state and
  dozens of vendored skills; a sync that mirrored deletions would turn "the repo has one skill" into
  "the agent lost the other 59". Live-only paths are reported as notes.
- **it never touches `config.yaml`, sessions, caches or state databases** — behaviour only, which is
  exactly `SOUL.md` plus `skills/**`.

An unknown profile is exit 2 (a silent pass would let a typo "sync" nothing), and `check` reports the
FIRST differing path by name and exits 1.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

TAG = "[agent-profile]"
MANIFEST = "agents/manifest.json"

#: Exit code for "this repository cannot answer the question" (unknown profile, unreadable manifest).
EXIT_USAGE = 2


def repo_root(start: Path | None = None) -> Path:
    """The checkout this script lives in."""
    return (start or Path(__file__).resolve().parent.parent).resolve()


def manifest(root: Path | None = None) -> list[dict]:
    """The profiles the repository carries, as `[{name, role}, ...]`.

    Accepts a bare list (the shape the issue writes) or `{"profiles": [...]}`, because both read
    naturally and the gate must not depend on which one a contributor picked.
    """
    path = (root or repo_root()) / MANIFEST
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"{TAG} FAILED: {path} is missing — the profiles are listed there (issue #791)") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{TAG} FAILED: {path} is not valid JSON: {exc}") from exc
    rows = data.get("profiles") if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise SystemExit(f"{TAG} FAILED: {path} must carry a non-empty list of profiles")
    out = []
    for row in rows:
        if isinstance(row, str):
            out.append({"name": row, "role": ""})
        elif isinstance(row, dict) and row.get("name"):
            out.append({"name": str(row["name"]), "role": str(row.get("role") or "")})
        else:
            raise SystemExit(f"{TAG} FAILED: {path}: every profile needs a `name` (got {row!r})")
    return out


def profile_dir(profile: str, root: Path | None = None) -> Path:
    """`agents/<profile>/` — where the repository keeps that agent's behaviour."""
    return (root or repo_root()) / "agents" / profile


def live_dir(profile: str, home: Path | None = None) -> Path:
    """The profile Hermes actually loads: `$HERMES_PROFILE_HOME` or `~/.hermes/profiles/<profile>`."""
    base = home or Path(os.environ.get("HERMES_PROFILE_HOME") or Path.home() / ".hermes" / "profiles")
    return Path(base) / profile


def carried_files(profile: str, root: Path | None = None) -> list[Path]:
    """Every file the repository carries for this profile, relative to `agents/<profile>/`."""
    base = profile_dir(profile, root)
    if not base.is_dir():
        raise SystemExit(f"{TAG} FAILED: {base} does not exist — the profile is listed in {MANIFEST} "
                         f"but its behaviour is not in the tree (issue #791)")
    return sorted(p.relative_to(base) for p in base.rglob("*") if p.is_file())


def sync(profile: str, *, root: Path | None = None, home: Path | None = None, check: bool = False) -> int:
    """Copy (or, with `check`, compare) `agents/<profile>/` into the live profile."""
    if profile not in {row["name"] for row in manifest(root)}:
        print(f"{TAG} FAILED: {profile!r} is not in {MANIFEST}; known: "
              f"{', '.join(row['name'] for row in manifest(root))}", file=sys.stderr)
        return EXIT_USAGE
    src, dst = profile_dir(profile, root), live_dir(profile, home)
    files = carried_files(profile, root)
    if check:
        differing, missing = [], []
        for rel in files:
            target = dst / rel
            if not target.exists():
                missing.append(str(rel))
            elif target.read_bytes() != (src / rel).read_bytes():
                differing.append(str(rel))
        live_only = sorted(str(p.relative_to(dst)) for p in dst.rglob("*")
                           if p.is_file() and p.relative_to(dst) not in set(files)) if dst.is_dir() else []
        for rel in live_only[:10]:
            print(f"{TAG} note: {dst / rel} exists only in the live profile (never deleted by a sync)")
        if missing or differing:
            print(f"{TAG} DRIFT: {dst} differs from agents/{profile}/", file=sys.stderr)
            for rel in missing:
                print(f"{TAG}   missing live: {rel}", file=sys.stderr)
            for rel in differing:
                print(f"{TAG}   differs: {rel}", file=sys.stderr)
            print(f"{TAG} run `make sync-agent-profile PROFILE={profile}` to make the tree authoritative",
                  file=sys.stderr)
            return 1
        print(f"{TAG} OK: {dst} matches agents/{profile}/ ({len(files)} file(s))")
        return 0
    written = unchanged = 0
    for rel in files:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        data = (src / rel).read_bytes()
        if target.exists() and target.read_bytes() == data:
            unchanged += 1
            continue
        target.write_bytes(data)
        written += 1
        print(f"{TAG} wrote {target}")
    print(f"{TAG} synced agents/{profile}/ -> {dst}: {written} written, {unchanged} unchanged")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Copy a host agent's in-tree behaviour into its live profile (#791).")
    ap.add_argument("cmd", choices=("sync", "check"))
    ap.add_argument("--profile", required=True, help="the profile name, as agents/manifest.json lists it")
    ap.add_argument("--root", default=None, help="the checkout to read (default: this script's parent)")
    ap.add_argument("--home", default=None, help="the profiles directory (default: $HERMES_PROFILE_HOME or ~/.hermes/profiles)")
    args = ap.parse_args(argv)
    root = Path(args.root) if args.root else repo_root()
    home = Path(args.home) if args.home else None
    return sync(args.profile, root=root, home=home, check=args.cmd == "check")


if __name__ == "__main__":
    sys.exit(main())
