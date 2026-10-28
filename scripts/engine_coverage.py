#!/usr/bin/env python3
"""Every shipped engine is BUILT by CI, or says why it is not an image (issue #771).

`skills-validate` proves a servable engine declares a container, and
`check-engine-params` proves the committed cell matches the skill. Neither proves the
cell is one the matrix will BUILD: `scripts/engine_image.DISABLED` drops a cell from
`list-engine-images CI=1`, a variant outside `CI_VARIANTS` is never a CI cell, and an
engine whose `os` omits `linux` has no image at all. A shipped engine in that state is
green everywhere and invisible to `make install` and `rank_engines`.

The pipeline order this closes is:

    registry -> skill -> params -> matrix cell -> build -> test -> publish -> install

This is the step between "params exist" and "the matrix builds them". It reads the
committed params (no Docker, no network) and gives each shipped skill one verdict:

  * ``built``        — a params variant that is a CI variant and not in ``DISABLED``;
  * ``not-an-image`` — deliberately not a container: ``servable: false``,
                       ``servable: via`` (rides another engine), or no ``linux`` in
                       ``os`` (a native Metal engine cannot run in an image);
  * ``unbuilt``      — servable on linux with no buildable cell. FAILS unless the
                       engine is recorded in ``KNOWN_UNBUILT`` with its reason and issue.

A ``KNOWN_UNBUILT`` entry whose engine is now built (or gone) is STALE and fails too, so
an exception cannot outlive the gap it records.

    python3 scripts/engine_coverage.py check     # the CI gate (exit 1 on a finding)
    python3 scripts/engine_coverage.py report    # the census, never fails
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import engine_image as ei  # noqa: E402  (the one source of DISABLED / CI_VARIANTS)
import engine_skills as es  # noqa: E402

# Cells that are shipped today and cannot be built yet. Each is tracked: removing the
# entry is what the issue does, and `check` fails a stale one.
KNOWN_UNBUILT: dict[str, str] = {
    "exllamav3-rocm": "#103 its only cell (rocm) is in DISABLED "
                      "(cuda_shim needs torch >= 2.13 ROCm headers)",
}


def variants_of(engine: str, params_dir: Path | None = None) -> dict[str, dict]:
    """The committed variants of one engine, from its params file ({} when absent)."""
    path = (params_dir or es.PARAMS_DIR) / f"{engine}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("variants") or {}


def verdict(skill: dict, variants: dict[str, dict], disabled=ei.disabled) -> tuple[str, str]:
    """(``built`` | ``not-an-image`` | ``unbuilt``, human reason) for one skill."""
    if skill.get("servable") is not True:
        return "not-an-image", f"servable: {skill.get('servable')} (rides another engine)"
    if "linux" not in (skill.get("os") or []):
        return "not-an-image", f"os: {skill.get('os')} (no linux image)"

    buildable = [v for v in variants if v in ei.CI_VARIANTS and not disabled(skill["id"], v)]
    if buildable:
        return "built", ", ".join(buildable)

    if not variants:
        return "unbuilt", "no params cell (run `make generate-engine-params`)"
    dropped = [f"{v} ({disabled(skill['id'], v) or 'not a CI variant'})" for v in variants]
    return "unbuilt", "no buildable CI cell: " + ", ".join(dropped)


def census(skills: dict[str, dict] | None = None,
           params_dir: Path | None = None) -> list[dict]:
    """One row per shipped skill: id, verdict, reason."""
    skills = es.load_skills() if skills is None else skills
    rows = []
    for sid, skill in sorted(skills.items()):
        skill = dict(skill, id=sid)
        v, reason = verdict(skill, variants_of(sid, params_dir))
        rows.append({"id": sid, "engine": skill.get("engine") or sid, "servable": skill.get("servable"),
                     "os": skill.get("os") or [], "verdict": v, "reason": reason})
    return rows


def findings(rows: list[dict], known: dict[str, str] | None = None) -> list[str]:
    """Every reason the gate must fail, naming the engine. ``known`` defaults to KNOWN_UNBUILT."""
    known = KNOWN_UNBUILT if known is None else known
    errors = []
    for row in rows:
        if row["verdict"] == "unbuilt" and row["id"] not in known:
            errors.append(f"{row['id']} ({row['engine']}) is shipped but never built: "
                          f"{row['reason']} — give it a buildable cell or record it in "
                          f"KNOWN_UNBUILT (#771)")
    verdicts = {row["id"]: row for row in rows}
    for engine, reason in sorted(known.items()):
        row = verdicts.get(engine)
        if row is None:
            errors.append(f"KNOWN_UNBUILT: {engine} has no skill any more — remove the entry ({reason})")
        elif row["verdict"] != "unbuilt":
            errors.append(f"KNOWN_UNBUILT: {engine} is {row['verdict']} now — the exception is "
                          f"stale, remove it ({reason})")
    return errors


DESCRIPTION = "Every shipped engine is built by CI, or says why it is not an image (issue #771)."


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("command", choices=("check", "report"))
    ap.add_argument("--skills", type=Path, default=None, help="skills tree (default: skills/engines)")
    ap.add_argument("--params", type=Path, default=None, help="params dir (default: containers/engines/params)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    rows = census(es.load_skills(a.skills), a.params)
    if a.json:
        print(json.dumps(rows, indent=1))
        return 0

    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in ("built", "not-an-image", "unbuilt")}
    print(f"[engine-coverage] {len(rows)} shipped skills; built {counts['built']}, "
          f"not-an-image {counts['not-an-image']}, unbuilt {counts['unbuilt']}")
    for row in rows:
        if row["verdict"] != "built":
            print(f"  {row['verdict']:<12} {row['id']:<28} {row['reason']}")
    if a.command == "report":
        return 0

    errors = findings(rows)
    if errors:
        for e in errors:
            print(f"[engine-coverage] FAIL {e}", file=sys.stderr)
        return 1
    print("[engine-coverage] OK every shipped engine is built by CI or deliberately not an image")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
