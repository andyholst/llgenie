"""A documentation review of an engine's derived build params, before the bump PR opens (issue #583).

`make engine-bump` proves the derived params **build**. It cannot prove they are **right for this
engine version and this arch**: the derive extractors are structural (CMake options, renames, recipe
`-D` flags, toolchain pins), so a flag the upstream's own docs now recommend — but which is missing from
the old params — is at best report-only and usually invisible.

This module is the deterministic half of the review leg. Hermes reads `params-review-in.md` (the engine's
docs at the pinned sha, its current params, the derive's findings) and writes `params-review.md` with
`PROPOSE` lines; this module then decides what may be written:

  * **the deterministic core stays the writer.** The agent cannot invent a flag: a proposal is applied
    only when the flag AND its quoted evidence both appear, verbatim, in the named upstream file at the
    pinned sha. Anything else is dropped and reported, never applied.
  * the engine's own `SKILL.md` is where the flag lands (its `cmake_flags.<backend>` string), because
    that is the only writer of params/Dockerfiles (`make generate-engine-params`).

`brief` writes the input, `apply` validates and writes, `--dry` prints the decision and mutates nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import engine_skills as es  # noqa: E402  (the one reader of a skill's front matter)

#: A proposal line, as the skill tells the agent to write it:
#:   PROPOSE <backend> <flag> DOC <repo-relative path> "<quote from that file>" WHY <reason>
PROPOSE = re.compile(
    r'^PROPOSE\s+(?P<backend>[A-Za-z0-9_-]+)\s+(?P<flag>-D[A-Za-z0-9_]+(?:=[^\s]+)?)\s+'
    r'DOC\s+(?P<doc>\S+)\s+"(?P<quote>[^"]+)"\s+WHY\s+(?P<why>.+)$')

#: How many bytes of an upstream file to carry into the brief. A README can be 100 KB; the review needs
#: the build/doc sections, not the whole file, and the agent's context is the budget.
DOC_BUDGET = 20_000

#: The files whose content a proposal may cite: the engine's docs and its backend recipes. A quote that
#: is not in one of these is not documentation.
DOC_GLOBS = ("README.md", "README.rst", "docs/**/*.md", "docs/**/*.rst", "CMakeLists.txt",
             "docker/**/Dockerfile*", "Dockerfile*", ".github/**/*.md")


def _show(repo_dir: Path, sha: str, path: str) -> str:
    """One file's content at `sha`, from a blobless clone. Empty when the path is absent."""
    r = subprocess.run(["git", "-C", str(repo_dir), "show", f"{sha}:{path}"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _clone(skill: dict) -> Path:
    """A `--filter=blob:none --no-checkout` clone of the engine's repo (same shape the derive uses)."""
    url = skill["repo"].rstrip("/")
    if "://" in url or url.startswith("git@"):
        url += ".git"
    dest = Path(tempfile.mkdtemp(prefix="llgenie-review-"))
    subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", url, str(dest)],
                   capture_output=True, text=True, timeout=300, check=True)
    return dest


def _docs(repo_dir: Path, sha: str) -> dict[str, str]:
    """{path: text} for the engine's documentation at `sha`, bounded per file."""
    listing = subprocess.run(["git", "-C", str(repo_dir), "ls-tree", "-r", "--name-only", sha],
                             capture_output=True, text=True)
    paths = [p for p in listing.stdout.splitlines() if p.strip()]
    out: dict[str, str] = {}
    for glob in DOC_GLOBS:
        for path in sorted(Path(p) for p in paths):
            if path.match(glob) or str(path) == glob:
                text = _show(repo_dir, sha, str(path))
                if text:
                    out[str(path)] = text[:DOC_BUDGET]
    return out


def _params(skill: dict) -> dict:
    """The engine's current build parameters, per backend, as the skill writes them."""
    return {"cmake_flags": skill.get("cmake_flags") or {},
            "hw_flags": skill.get("hw_flags") or {},
            "binary_flags": skill.get("binary_flags") or []}


def brief(engine: str, out: Path | None = None) -> Path:
    """Write `params-review-in.md`: the engine's docs at its pin, its params, and what to answer."""
    skill = es.get_skill(engine)
    sha = skill["pinned"]
    repo_dir = _clone(skill)
    docs = _docs(repo_dir, sha)
    out = out or Path("params-review-in.md")
    lines = [
        f"# Build-parameter documentation review — {skill['id']} @ {sha[:8]}",
        "",
        f"Pinned upstream: {skill['repo']} @ `{sha}`. Review the parameters THIS repo builds with",
        "against what the engine's own documentation says for each backend.",
        "",
        "## Current build parameters (from skills/engines/" f"{skill['id']}/SKILL.md)",
        "",
        "```yaml",
        *(f"{k}: {json.dumps(v)}" for k, v in _params(skill).items()),
        "```",
        "",
        "## Upstream documentation at this pin",
        "",
        *(f"### {path}\n\n```\n{text}\n```\n" for path, text in docs.items()),
        "## What to answer",
        "",
        "For every parameter the documentation requires (or recommends, or marks per-arch) that the",
        "current parameters do not carry, write ONE line per parameter:",
        "",
        '`PROPOSE <backend> <-DFLAG or -DFLAG=value> DOC <repo-relative path> "<quote from that file>" WHY <reason>`',
        "",
        "- the backend must be one of the engine's backends (`cuda`, `rocm`, `vulkan`, `cpu`, `metal`)",
        "  or `common`;",
        "- the flag must be exactly what the documentation uses (CMake `-D` form, `NAME=VALUE` when the",
        "  docs give a value);",
        "- the quote must be copied verbatim from the named file, because the host checks it and DROPS",
        "  any proposal whose quote or flag is not there;",
        "- if the documentation says nothing you can quote, write `NO REVIEW: <reason>` and propose",
        "  nothing. Reporting nothing is a correct answer; an uncited flag is not.",
        "",
    ]
    out.write_text("\n".join(lines))
    print(f"[params-review] {skill['id']}: {len(docs)} documentation file(s) at {sha[:8]} -> {out}")
    return out


def parse_proposals(text: str) -> list[dict]:
    """The agent's `PROPOSE` lines, in order. Malformed lines are ignored (and counted by the caller)."""
    out = []
    for line in (text or "").splitlines():
        m = PROPOSE.match(line.strip())
        if m:
            out.append(m.groupdict())
    return out


def _flags_in(value: str) -> set[str]:
    """The `-DNAME` tokens already present in one cmake_flags string."""
    return set(re.findall(r"-D[A-Za-z0-9_]+", value or ""))


def validate(proposals: list[dict], docs: dict[str, str], skill: dict) -> tuple[list[dict], list[str]]:
    """Split the proposals into (accepted, rejected-with-reason). Pure, so the rule is testable.

    A proposal is accepted ONLY when its flag and its quoted evidence both appear in the named
    upstream file, and the backend is one this engine builds. Everything else is dropped and said out
    loud — an uncited flag is exactly what this leg exists to refuse.
    """
    accepted: list[dict] = []
    rejected: list[str] = []
    backends = list(skill.get("backends") or []) + ["common"]
    for p in proposals:
        backend, flag, doc, quote = p["backend"], p["flag"], p["doc"], p["quote"]
        if backend not in backends:
            rejected.append(f"{backend} {flag}: `{backend}` is not one of this engine's backends "
                            f"({', '.join(backends)})")
            continue
        if doc not in docs:
            rejected.append(f"{backend} {flag}: no upstream file `{doc}` at this pin")
            continue
        text = docs[doc]
        # A CMake flag is `-DNAME=value`; the upstream file names it `NAME` (option(...)/set(...)),
        # so the DOCUMENTED test is on NAME, and the "already present" test is on the full `-DNAME`.
        bare = flag.split("=", 1)[0].removeprefix("-D")
        if not bare or bare not in text:
            rejected.append(f"{backend} {flag}: `{bare}` does not appear in `{doc}`")
            continue
        if " ".join(quote.split()) not in " ".join(text.split()):
            rejected.append(f"{backend} {flag}: the quoted evidence is not in `{doc}`")
            continue
        current = (skill.get("cmake_flags") or {}).get(backend) or \
                  ((skill.get("cmake_flags") or {}).get("common") or "" if backend != "common" else "")
        if f"-D{bare}" in _flags_in(current):
            rejected.append(f"{backend} {flag}: already in the params for `{backend}`")
            continue
        accepted.append(p)
    return accepted, rejected


def apply_accepted(engine: str, accepted: list[dict], dry: bool = False) -> list[str]:
    """Append the accepted flags to the skill's `cmake_flags.<backend>`. The skill is the writer."""
    path = es.SKILLS_DIR / engine / "SKILL.md"
    text = path.read_text()
    changed: list[str] = []
    for p in accepted:
        backend, flag = p["backend"], p["flag"]
        # The frontmatter line for this backend: `  <backend>: "-DA=ON -DB=ON"` under cmake_flags.
        block = re.search(r"(?ms)^cmake_flags:\n(?P<body>(?:[ \t]+.*\n)+)", text)
        if not block:
            raise SystemExit(f"[params-review] {engine}: SKILL.md has no cmake_flags block to extend")
        line = re.search(rf'(?m)^(?P<ind>[ \t]+){re.escape(backend)}:[ \t]*(?P<val>"[^"]*"|[^\n]*)\n',
                         block.group("body"))
        if not line:
            raise SystemExit(f"[params-review] {engine}: cmake_flags has no `{backend}` line; "
                             f"refusing to invent one")
        old_val = line.group("val").strip()
        quoted = len(old_val) >= 2 and old_val[0] == '"' and old_val[-1] == '"'
        inner = old_val[1:-1] if quoted else old_val
        # The skill writes these strings quoted (a value may contain spaces); keep the shape.
        new_val = f'"{(inner + " " + flag).strip()}"' if quoted else (inner + " " + flag).strip()
        text = text.replace(line.group(0), f"{line.group('ind')}{backend}: {new_val}\n", 1)
        changed.append(f"{backend} +{flag}")
    if changed and not dry:
        path.write_text(text)
    return changed


def section(engine: str, accepted: list[dict], rejected: list[str]) -> str:
    """The `Documentation review` section the bump PR carries."""
    lines = ["## Documentation review", ""]
    if not accepted and not rejected:
        lines += ["No documentation-sourced parameter was proposed for this pin: the derived params "
                  "stand as they are.", ""]
        return "\n".join(lines)
    if accepted:
        lines += [f"Applied from the engine's own documentation ({len(accepted)}):", ""]
        for p in accepted:
            lines.append(f"- `{p['backend']}` **{p['flag']}** — `{p['doc']}`: \"{p['quote'][:160]}\"")
        lines.append("")
    if rejected:
        lines += [f"Proposed but **not applied** ({len(rejected)}) — each was refused by the host "
                  "because the documentation does not support it:", ""]
        lines += [f"- {r}" for r in rejected]
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("command", choices=["brief", "apply"])
    ap.add_argument("--engine", required=True)
    ap.add_argument("--file", default="params-review.md", help="the agent's proposals")
    ap.add_argument("--section", default="params-review-section.md", help="where the PR section goes")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)

    if a.command == "brief":
        brief(a.engine)
        return 0

    skill = es.get_skill(a.engine)
    sha = skill["pinned"]
    repo_dir = _clone(skill)
    docs = _docs(repo_dir, sha)
    text = Path(a.file).read_text() if Path(a.file).exists() else ""
    if not text.strip():
        print(f"[params-review] {a.engine}: the review leg wrote no {a.file}; nothing to apply")
        Path(a.section).write_text(section(a.engine, [], []))
        return 0
    proposals = parse_proposals(text)
    accepted, rejected = validate(proposals, docs, skill)
    changed = apply_accepted(a.engine, accepted, dry=a.dry) if accepted else []
    if changed and not a.dry:
        # The skill is the writer: regenerate the params and per-arch Dockerfiles from it.
        subprocess.run(["make", "generate-engine-params", f"ENGINE={a.engine}"],
                       capture_output=True, text=True, timeout=300)
        print(f"[params-review] {a.engine}: regenerated params/Dockerfiles for {', '.join(changed)}")
    Path(a.section).write_text(section(a.engine, accepted, rejected))
    print(f"[params-review] {a.engine}: {len(accepted)} applied, {len(rejected)} rejected "
          f"({len(proposals)} proposal(s)); section -> {a.section}")
    for line in rejected:
        print(f"[params-review]   dropped: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
