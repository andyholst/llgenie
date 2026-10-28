#!/usr/bin/env python3
"""A bot leg proves it starts from current `main` and read the rulebook (issue #792).

A leg used to start from whatever tree it was handed, and nothing recorded which `AGENTS.md` it
obeyed. Two measured facts on 2026-10-28: the owner's checkout sat four commits behind
`origin/main` and no bot flow computed that, and `AGENTS.md` is 87,255 bytes / 1,302 lines that
changed four times in one week — a branch cut before a rule changed applies the old rule, and the
PR could not be read against the rulebook it actually used.

The preflight answers both, in one code path:

    git fetch <remote> <branch>                       # a bot that cannot see main must not start
    the GitHub slug of <remote> must be asimov-agent/llgenie
    a dirty working tree is refused                   # run inputs are gitignored, so they do not count
    HEAD must CONTAIN <remote>/<branch>               # ahead is fine, behind is fast-forwarded
    git merge --ff-only <remote>/<branch>             # never a rebase, never a reset
    a diverged tree is refused with the left/right counts

It then writes `preflight.txt` at the repository root — a run input, gitignored like `issue.md`,
never repo content — carrying the line a PR body repeats:

    AGENTS: <main sha> <bytes>b <lines>l
    AGENTS-HEADINGS: sha256:<digest of the `## ` heading list>
    MAIN: <main sha>
    TREE: <short head> <at|ahead|fast-forwarded>
    PROFILE: <the leg that ran this>
    WHEN: <utc>

The heading digest is what a rule change moves: rewording a sentence inside an existing section
leaves it alone, adding or renaming a `## ` heading changes it.

Commands:
    bot_preflight.py                 verify the tree and write preflight.txt
    bot_preflight.py --check         verify the tree, then name the FIRST field that disagrees with
                                     an existing preflight.txt (a leg that reused a stale file)

Exit codes: 0 verified, 2 refused (stale / diverged / dirty / unreachable / wrong origin / stale
record). There is no partial pass: a leg that cannot prove its base and its rulebook does not start.

Usage:
    python3 scripts/bot_preflight.py
    python3 scripts/bot_preflight.py --check
    python3 scripts/bot_preflight.py --remote origin --branch main --profile issue-bot-triage
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
#: The rules every leg obeys. Its size, line count and heading list are what the preflight records.
AGENTS = "AGENTS.md"
#: The run input the preflight writes (gitignored; never committed, like `issue.md`).
PREFLIGHT = "preflight.txt"
#: The upstream this repository's bots work against. A checkout pointed anywhere else is refused.
REQUIRED_SLUG = "asimov-agent/llgenie"
DEFAULT_REMOTE = "origin"
DEFAULT_BRANCH = "main"
#: A `## ` heading, which is where a RULE lives (prose below it is not a rule change on its own).
HEADING = re.compile(r"^## .*$", re.M)
#: `https://github.com/<owner>/<repo>.git` and `git@github.com:<owner>/<repo>.git`.
GITHUB_URL = re.compile(r"^(?:https?://|ssh://git@|git@)github\.com[:/]+(?P<slug>[^/]+/[^/]+?)(?:\.git)?/?$")
#: The recorded line a PR body repeats verbatim.
AGENTS_LINE = re.compile(r"^AGENTS: (?P<sha>[0-9a-f]{40}) (?P<bytes>\d+)b (?P<lines>\d+)l$", re.M)


class Refused(Exception):
    """A refusal: the leg must not start, and the message says what the preflight read."""


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def _out(root: Path, *args: str) -> str:
    proc = git(root, *args)
    if proc.returncode != 0:
        raise Refused(f"`git {' '.join(args)}` failed: {(proc.stderr or proc.stdout).strip()}")
    return proc.stdout.strip()


def slug_of(url: str) -> str | None:
    """The GitHub `owner/repo` a remote URL names, or None when it is not a GitHub URL.

    None is not a refusal: a clone whose remote is a local path is a testing/mirror remote and the
    preflight says so, which is how `tests/test_bot_preflight.py` drives a real fetch and a real
    fast-forward without reaching GitHub. A GitHub URL that names ANOTHER repository IS a refusal.
    """
    m = GITHUB_URL.match(url.strip())
    return m.group("slug") if m else None


def agents_record(text: str) -> tuple[int, int, str]:
    """`AGENTS.md` as the preflight records it: bytes, lines (`wc -l`), and the heading digest."""
    data = text.encode("utf-8")
    digest = hashlib.sha256("\n".join(m.group(0) for m in HEADING.finditer(text)).encode()).hexdigest()
    return len(data), text.count("\n"), digest


def agents_line(sha: str, text: str) -> str:
    """The exact line a PR body carries: `AGENTS: <sha> <bytes>b <lines>l`."""
    size, lines, _ = agents_record(text)
    return f"AGENTS: {sha} {size}b {lines}l"


def parse_agents_line(text: str) -> dict[str, str] | None:
    """The first `AGENTS:` line in a body, as its parts — the shape both sides agree on."""
    m = AGENTS_LINE.search(text or "")
    if not m:
        return None
    return m.groupdict()


def _status_paths(root: Path, limit: int = 5) -> list[str]:
    """The paths a dirty tree carries, as `git status --porcelain` names them.

    The two status columns are read from the RAW line: stripping the output first would eat the
    leading space of ` M <path>` and slice the first character off the path.
    """
    proc = git(root, "status", "--porcelain")
    if proc.returncode != 0:
        raise Refused(f"`git status` failed: {(proc.stderr or proc.stdout).strip()}")
    return [line[3:] for line in proc.stdout.splitlines() if line.strip()][:limit]


def verify(root: Path, remote: str, branch: str) -> dict:
    """Fetch, check the origin, check the tree, and bring it to `<remote>/<branch>` or refuse."""
    if not (root / AGENTS).is_file():
        raise Refused(f"{AGENTS} is not in {root} — there is no rulebook to read")

    if git(root, "rev-parse", "--git-dir").returncode != 0:
        raise Refused(f"{root} is not a git checkout")

    url = _out(root, "remote", "get-url", remote)
    slug = slug_of(url)
    if slug is not None and slug != REQUIRED_SLUG:
        raise Refused(
            f"`{remote}` is {url} ({slug}), not {REQUIRED_SLUG}: a leg works against this "
            f"repository's `main`, so point `{remote}` there (REMOTE=<name> picks another remote)"
        )
    note = None if slug else f"`{remote}` is {url}, not a GitHub URL: accepted as a local/mirror remote"

    proc = git(root, "fetch", remote, branch, "--quiet")
    if proc.returncode != 0:
        raise Refused(
            f"cannot fetch {remote}/{branch}: {(proc.stderr or proc.stdout).strip()} — "
            f"refusing to start on a stale base"
        )
    target = _out(root, "rev-parse", "FETCH_HEAD")

    dirty = _status_paths(root)
    if dirty:
        raise Refused(
            "the working tree has uncommitted changes ("
            + ", ".join(dirty)
            + f"): a preflight reads a clean tree. Bot run inputs such as {PREFLIGHT} and issue.md "
            "are gitignored, so they do not appear here"
        )

    head = _out(root, "rev-parse", "HEAD")
    if head == target:
        state = "at"
    elif git(root, "merge-base", "--is-ancestor", target, "HEAD").returncode == 0:
        ahead = _out(root, "rev-list", "--count", f"{target}..HEAD")
        state = f"ahead ({ahead} commit(s) on top of {remote}/{branch})"
    else:
        counts = _out(root, "rev-list", "--left-right", "--count", f"HEAD...{target}").split()
        ahead, behind = (counts + ["?", "?"])[:2]
        proc = git(root, "merge", "--ff-only", target, "--quiet")
        if proc.returncode != 0:
            raise Refused(
                f"HEAD is diverged from {remote}/{branch}: git rev-list --left-right --count "
                f"HEAD...{remote}/{branch} = {ahead} (HEAD-only) {behind} (main-only), so it cannot "
                f"fast-forward. Rebase or reset the tree yourself; the preflight never rewrites it"
            )
        state = f"fast-forwarded ({behind} commit(s) from {remote}/{branch})"
        head = target

    size, lines, digest = agents_record((root / AGENTS).read_text(encoding="utf-8"))
    return {
        "note": note,
        "sha": target,
        "head": head,
        "state": state,
        "bytes": size,
        "lines": lines,
        "digest": digest,
        "line": f"AGENTS: {target} {size}b {lines}l",
    }


def render(root: Path, result: dict, profile: str) -> str:
    """The `preflight.txt` body: the AGENTS line first (a PR body repeats it), then the evidence."""
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return "\n".join([
        result["line"],
        f"AGENTS-HEADINGS: sha256:{result['digest']}",
        f"MAIN: {result['sha']}",
        f"TREE: {result['head'][:12]} {result['state']}",
        f"PROFILE: {profile or '-'}",
        f"WHEN: {when}",
    ]) + "\n"


def first_difference(recorded: str, live: dict) -> tuple[str, str, str] | None:
    """The FIRST field that disagrees between a recorded preflight.txt and the live values."""
    fields = [line.split(": ", 1) for line in recorded.splitlines() if ": " in line]
    seen = {k: v for k, v in fields}
    # The AGENTS line is `AGENTS: <value>`, so its recorded value is everything after that prefix.
    for key, want in (("AGENTS", live["line"][len("AGENTS: "):]),
                      ("AGENTS-HEADINGS", f"sha256:{live['digest']}"),
                      ("MAIN", live["sha"])):
        got = seen.get(key)
        if got is None:
            return key, "(missing)", want
        if got != want:
            return key, got, want
    return None


def run(root: Path, remote: str, branch: str, profile: str, check: bool) -> int:
    try:
        result = verify(root, remote, branch)
    except Refused as exc:
        print(f"[bot-preflight] REFUSED: {exc}", file=sys.stderr)
        return 2

    if result["note"]:
        print(f"[bot-preflight] note: {result['note']}")
    body = render(root, result, profile)
    if check:
        recorded_path = root / PREFLIGHT
        if not recorded_path.is_file():
            print(f"[bot-preflight] REFUSED: no {PREFLIGHT} to compare against — a leg that never "
                  f"ran the preflight has no record of the rulebook it read", file=sys.stderr)
            return 2
        diff = first_difference(recorded_path.read_text(encoding="utf-8"), result)
        if diff:
            key, got, want = diff
            print(f"[bot-preflight] REFUSED: {PREFLIGHT} is stale: {key} is `{got}`, live is "
                  f"`{want}`", file=sys.stderr)
            return 2
        print(f"[bot-preflight] OK: {PREFLIGHT} matches the live tree ({result['state']})")
        print(f"[bot-preflight] {result['line']}")
        return 0

    (root / PREFLIGHT).write_text(body, encoding="utf-8")
    print(f"[bot-preflight] OK: tree is {result['state']} ({remote}/{branch} {result['sha'][:12]})")
    print(f"[bot-preflight] {result['line']}")
    print(f"[bot-preflight] wrote {PREFLIGHT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bot_preflight", description=__doc__)
    p.add_argument("--root", default=str(REPO_ROOT), help="tree to verify and to write preflight.txt in")
    p.add_argument("--remote", default=DEFAULT_REMOTE)
    p.add_argument("--branch", default=DEFAULT_BRANCH)
    p.add_argument("--profile", default="", help="the leg that ran this, recorded in preflight.txt")
    p.add_argument("--check", action="store_true",
                   help="compare an existing preflight.txt to the live values instead of writing one")
    args = p.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"[bot-preflight] REFUSED: {root} is not a directory", file=sys.stderr)
        return 2
    return run(root, args.remote, args.branch, args.profile, args.check)


if __name__ == "__main__":
    sys.exit(main())
