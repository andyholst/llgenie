#!/usr/bin/env python3
"""Which stages a pull request's diff selects (issue #824, part a).

CI ran one pipeline for every change: a seven-file markdown PR queued the same 28 jobs as a change to
`containers/engines/`, so a runner minute spent building an engine image for a markdown edit was a minute
not spent giving a real engine change its verdict. This is the classifier that reads the diff ONCE and
says, out loud, which classes it found and which jobs they select.

    python3 scripts/ci_scope.py --base origin/main      # a pull_request run (the PR's base ref)
    python3 scripts/ci_scope.py --before <sha>          # a push run (the commit before the push)
    python3 scripts/ci_scope.py --paths a.md tests/x.py # an explicit list, no git
    python3 scripts/ci_scope.py --all                   # every class, for a push to main

WHAT IT IS NOT: it does not skip a job. A job-level `if:` that skips a stage is invisible in the job
list (`tests/test_ci_images.py::test_no_ci_step_or_job_is_skipped` permits exactly five such shapes and
none of them is a path selection), so part (a) selects the docs class at the TRIGGER
(`pull_request.paths-ignore` in `ci.yml`) and prints the full decision here; per-stage selection inside
`ci.yml` for the code classes is part (b), #824.

THE CONTRACT:

- **one class per rule**, matched by glob where `*` stops at `/` and `**` crosses it;
- **a wildcard path selects every class**: `Makefile`, `tools/**`, `.github/**`, `scripts/ci_*.py`,
  `scripts/engine_*.py`, `scripts/check_*.py`, `pytest.ini`, `.gitleaks.toml`, `renovate.json`,
  `AGENTS.md` can change what ANY gate proves, so a quiet skip there would hide a regression in the
  gate itself;
- **an unmatched path is a LOUD failure** (exit 1 naming the path), never a silent pass: a path nobody
  classified is a stage nobody decided about;
- `guard` and `lint` always run (they authorize publishing and hold the markdown gate), and `push` runs
  to `main` keep the whole matrix — absence is safe for merging but dangerous for reading (#801, #817).

Stdlib only: it runs in the runner with no dependency, and in `ci-unit` on the host.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TAG = "[ci-scope]"

#: Exit code for a path no class claims, or a diff we could not read.
EXIT_UNCLASSIFIED = 1

#: class -> the globs it owns. Order is the order the report prints them in.
CLASSES: dict[str, tuple[str, ...]] = {
    "docs": ("*.md", "docs/**", "agent-wiki/**", "openspec/**"),
    "skills": (".hermes/**", "agents/**"),
    "workflows": (".github/**",),
    "scripts": ("scripts/**", "tools/**"),
    "tests": ("tests/**",),
    "data": ("data/**",),
    "containers": ("containers/**",),
    "engines": ("containers/engines/**", "skills/engines/**"),
    "security": ("renovate.json", "security-reports/**", "tools/security-floors.in"),
}

#: A path matching one of these selects EVERY class: it can change what any gate proves.
WILDCARDS: tuple[str, ...] = (
    "Makefile",
    "tools/**",
    ".github/**",
    "scripts/ci_*.py",
    "scripts/engine_*.py",
    "scripts/check_*.py",
    "pytest.ini",
    ".gitleaks.toml",
    "renovate.json",
    "AGENTS.md",
)

#: The classes that select `ci-images`: everything but `docs`, because a docs-only diff needs no image.
_NON_DOCS = tuple(name for name in CLASSES if name != "docs")

#: The `docs` class as a GitHub `paths-ignore` list — the globs a docs-only diff must match, MINUS the
#: wildcards (`AGENTS.md` is a `*.md`, and editing it must re-include the full matrix). `ci.yml` and this
#: constant are compared by `tests/test_ci_scope.py`, so the YAML cannot drift from the classifier.
DOCS_TRIGGER_IGNORE: tuple[str, ...] = (
    "*.md",
    "!AGENTS.md",
    "docs/**",
    "agent-wiki/**",
    "openspec/**",
)

#: job -> the classes that select it (`None` = always runs). The 28 jobs of `ci.yml`, in file order
#: (issue #824's table). Two rows are families: `engine-image` / `test-published` are matrix rows and
#: `install-published-*` is one job per backend.
_STAGES = {
    "lint": None,
    "unit": ("scripts", "tests", "data", "skills", "containers", "workflows"),
    "install": ("scripts", "containers", "engines", "skills", "data"),
    "agents-read": ("skills",),
    "openspec": ("docs",),
    "top-tier": ("data", "scripts", "containers"),
    "cpu-health": ("engines", "containers", "scripts"),
}

JOBS: tuple[tuple[str, tuple[str, ...] | None], ...] = (
    ("guard", None),
    ("ci-images", _NON_DOCS),
    ("scanner-images", ("containers", "security")),
    ("engine-base", ("engines", "containers")),
    ("engine-matrix", ("engines", "containers", "skills")),
    ("engine-image", ("engines", "containers", "skills")),
    ("engine-published-test", ("engines", "containers", "skills")),
    ("linux-published", ("engines", "containers")),
    ("linux/lint", None),
    ("linux/unit", _STAGES["unit"]),
    ("linux/install", _STAGES["install"]),
    ("linux/agents-read", _STAGES["agents-read"]),
    ("linux/openspec", _STAGES["openspec"]),
    ("linux/top-tier", _STAGES["top-tier"]),
    ("linux/cpu-health", _STAGES["cpu-health"]),
)


def glob_to_regex(pattern: str) -> str:
    """Translate one path glob to a regex: `*` stops at `/`, `**` crosses it, everything else literal."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?" )  # zero or more directories
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return "".join(out)


def matches(pattern: str, path: str) -> bool:
    """Does `path` match `pattern` under the classifier's glob rules?"""
    return re.fullmatch(glob_to_regex(pattern), path) is not None


def matched_wildcards(paths: list[str]) -> list[str]:
    """The wildcard globs the diff matched — the reason every class is selected."""
    return [pattern for pattern in WILDCARDS if any(matches(pattern, p) for p in paths)]


def classify(paths: list[str]) -> tuple[list[str], list[str]]:
    """The classes the diff selects, and the paths no class claims.

    A wildcard short-circuits: every class is selected, because such a path can change what any gate
    proves. Otherwise a class is selected by the first of its globs that matches any path.
    """
    if matched_wildcards(paths):
        return list(CLASSES), []
    selected: list[str] = []
    unmatched: list[str] = []
    for path in paths:
        hit = [name for name, globs in CLASSES.items() if any(matches(g, path) for g in globs)]
        if not hit:
            unmatched.append(path)
            continue
        for name in hit:
            if name not in selected:
                selected.append(name)
    return [name for name in CLASSES if name in selected], unmatched


def select(classes: list[str]) -> list[tuple[str, bool, str]]:
    """One `(job, runs, why)` row per job of `ci.yml`, decided by the classes the diff selected."""
    wanted = set(classes)
    rows: list[tuple[str, bool, str]] = []
    for job, needs in JOBS:
        if needs is None:
            rows.append((job, True, "always"))
            continue
        hit = [name for name in needs if name in wanted]
        if hit:
            rows.append((job, True, f"class {'+'.join(hit)}"))
        else:
            rows.append((job, False, f"no class from [{','.join(classes) or '-'}]; needs one of {','.join(needs)}"))
    return rows


def changed_paths(*, base: str | None, before: str | None, cwd: str | None = None) -> list[str]:
    """The diff's paths, read from git — the same `before`/base-ref logic `ci.yml`'s engine-matrix uses."""
    if base and before:
        raise ValueError("give --base (a pull request) or --before (a push), not both")
    if not base and not before:
        raise ValueError("one of --base / --before / --paths is required")
    revision = before or f"{base}...HEAD"
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", revision],
        cwd=cwd, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff {revision} failed: {(result.stderr or result.stdout).strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def report(classes: list[str], rows: list[tuple[str, bool, str]], paths: list[str], wildcards: list[str]) -> list[str]:
    """The lines a run prints: what was read, the class per rule, then every job with its verdict."""
    lines = [f"{TAG} {len(paths)} file(s) changed"]
    for name in classes:
        lines.append(f"{TAG} class={name}")
    for pattern in wildcards:
        lines.append(f"{TAG} wildcard={pattern} — selects every class")
    for job, runs, why in rows:
        lines.append(f"{TAG} job={job} {'run' if runs else 'skip'} — {why}")
    selected = [job for job, runs, _ in rows if runs]
    lines.append(
        f"{TAG} scope: class(es) {','.join(classes) or '-'} -> {len(selected)} of {len(rows)} job(s): "
        f"{','.join(selected)}"
    )
    if "docs" in classes and set(classes) == {"docs"}:
        lines.append(
            f"{TAG} trigger: a docs-only diff does not start ci.yml at all (`pull_request.paths-ignore`); "
            f"the docs gates run in scope.yml, and the `scope` check states this decision (#824)"
        )
    return lines


def github_output(rows: list[tuple[str, bool, str]], classes: list[str], path: Path | None) -> None:
    """Write the machine-readable answer GitHub needs a step to export."""
    if path is None:
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"classes={','.join(classes)}\n")
        handle.write(f"jobs={' '.join(job for job, runs, _ in rows if runs)}\n")
        handle.write("docs_only=%d\n" % int(set(classes) == {"docs"}))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select CI stages from a pull request's changed paths (#824).")
    parser.add_argument("--base", default=None, help="the PR base ref, e.g. origin/main (diffs <base>...HEAD)")
    parser.add_argument("--before", default=None, help="the commit before a push (github.event.before)")
    parser.add_argument("--paths", nargs="*", default=None, help="an explicit path list instead of a git diff")
    parser.add_argument("--paths-from", default=None, help="read the path list from a file ('-' for stdin)")
    parser.add_argument("--all", action="store_true", help="select every class (a push to main keeps the full matrix)")
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"),
                        help="append classes=/jobs=/docs_only= to this file (default: $GITHUB_OUTPUT)")
    parser.add_argument("--cwd", default=None, help="the repository to diff (default: the current directory)")
    args = parser.parse_args(argv)

    try:
        if args.paths is not None:
            paths = list(args.paths)
        elif args.paths_from:
            text = sys.stdin.read() if args.paths_from == "-" else Path(args.paths_from).read_text()
            paths = [line.strip() for line in text.splitlines() if line.strip()]
        elif args.all:
            paths = []
        else:
            paths = changed_paths(base=args.base, before=args.before, cwd=args.cwd)
    except (ValueError, RuntimeError) as exc:
        print(f"{TAG} FAILED: {exc}", file=sys.stderr)
        return EXIT_UNCLASSIFIED

    wildcards = matched_wildcards(paths)
    classes, unmatched = (list(CLASSES), []) if args.all else classify(paths)
    if args.all:
        wildcards = ["--all"]
    rows = select(classes)
    for line in report(classes, rows, paths, wildcards):
        print(line)

    if unmatched:
        for path in unmatched:
            print(f"{TAG} FAILED: {path} matches no class — add it to CLASSES in scripts/ci_scope.py "
                  f"(or to WILDCARDS when it can change what any gate proves)", file=sys.stderr)
        return EXIT_UNCLASSIFIED

    github_output(rows, classes, Path(args.github_output) if args.github_output else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
