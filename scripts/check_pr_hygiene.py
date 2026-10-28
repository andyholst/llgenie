#!/usr/bin/env python3
"""A commit message and a PR body state the issue, the fix and the benefit (issue #313), and a PR
closes the issue it implements (issue #324).

A reviewer who reads a commit or a PR must learn three things without opening the issue: **what the
issue was**, **how the change solves it**, and **what the benefit is** — plus the technical detail
(files, tests, gates, measured numbers) that lets them verify the claim. A subject-only commit or an
empty PR body carries none of that, so this guard makes both a red `ci-unit` instead of a habit. The
closing rule is the other half: a PR that implements an issue MUST close it (`closes #<n>`), so the
issue's state stays evidence about the code — measured on `main` (`4d999e3`), 13 of the last 38
merged PRs closed nothing.

It reads the producers the repository OWNS — `.github/workflows/*.yml`, the `Makefile`,
`scripts/**/*.sh` (shell invocations) and `scripts/**/*.py` (an argv list handed to the repo's `_gh`
helper) — extracts every commit and every PR open they run, and reports:

* `commit-message`      a commit with no message, a placeholder message, a subject that is not a
                        typed Conventional Commit, or no body (a bare subject);
* `pr-body`             a PR opened with no body, or a body that is empty / a placeholder;
* `agents-mandate`      an `AGENTS.md` that no longer carries the message mandate, so the rule
                        cannot be deleted silently;
* `agents-closing-rule` an `AGENTS.md` that no longer states that a PR closes the issue it
                        implements, so the closing rule cannot be deleted silently either;
* `pr-agents-line`      a PR body whose `AGENTS: <sha> <bytes>b <lines>l` line is missing, names a
                        sha that is not `git merge-base origin/main HEAD`, or carries counts that
                        are not those of `AGENTS.md` at that sha.

The `AGENTS:` line is how a reviewer reads which rulebook the work obeyed, so a body without it (or
with a line taken from an older `main`) is the same defect as a body that states no benefit. The
body itself is read WITHOUT network when one is available: `--pr-body`, `--pr-body-file`,
`$PR_BODY_FILE` (the implementer's `pr-body.md`, so a missing line is caught before the PR opens),
`$GITHUB_EVENT_PATH`'s `pull_request.body` inside `ci-unit`; `--pr <n> --repo <slug>` is the one
path that calls `gh`. On a push to `main` there is no PR body at all: that half reports what it read
and the static half still decides the exit code.

A producer that opens a PR through a variable or a file is accepted — the guard checks that a real
body is PASSED, and the producers' own tests pin what that body says. Message content (the
Issue/Fix/Benefit parts and the technical extension) is stated in AGENTS.md and pinned by
`tests/test_pr_hygiene.py`.

Commands:
    check_pr_hygiene.py check     exit non-zero on any violation, and list them
    check_pr_hygiene.py report    print every producer and what its messages pass

Usage:
    python3 scripts/check_pr_hygiene.py check
    python3 scripts/check_pr_hygiene.py report
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ".github/workflows"
SCRIPTS = "scripts"
AGENTS = "AGENTS.md"
#: The line a bot PR body carries, verbatim: `AGENTS: <main sha> <bytes>b <lines>l` (issue #792).
AGENTS_LINE = re.compile(r"(?m)^AGENTS: (?P<sha>[0-9a-f]{40}) (?P<bytes>\d+)b (?P<lines>\d+)l$")
#: What that line must look like, quoted in a finding so a reader can fix it without the spec.
AGENTS_LINE_SHAPE = "AGENTS: <sha of a main this branch contains> <bytes of AGENTS.md at that sha>b <lines>l"
#: The identity this repository's bots commit as. A PR is a BOT PR when every commit it adds is
#: authored by it — the human identity is `andy.holst@protonmail.com` (see `check_pr_authors.py`).
BOT_EMAIL = "support@docondee.com"
#: The mandate heading AGENTS.md must carry. Deleting it is a violation, not an edit.
AGENTS_MANDATE = "## Every PR body and commit message carries the issue, the fix and the benefit"
#: The closing rule AGENTS.md must carry — a PR that implements an issue closes it. The loophole
#: ("if the PR does not close an issue, still end with the issue reference") is what this forbids.
AGENTS_CLOSING_RULE = "A PR that implements an issue MUST close it"
#: A typed Conventional Commit subject: `type(scope): summary`.
CONVENTIONAL = re.compile(r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
                          r"(\([^)]+\))?!?: \S")
#: A message that says nothing. Compared case-insensitively after trimming.
PLACEHOLDERS = {"", "-", "--", "wip", "update", "fix", "msg", "tbd", "todo", "n/a", "na",
                "x", ".", "none", "nothing", "nop"}
#: The invocations this guard governs, as a shell command runs them.
GIT_COMMIT = re.compile(r"\bgit\s+commit\b")
GH_PR_CREATE = re.compile(r"\bgh\s+pr\s+create\b")
#: The same invocations as a Python argv list handed to `_gh(gh, [...])`.
PY_GIT_COMMIT = re.compile(r"""["']git["']\s*,\s*["']commit["']""")
PY_PR_CREATE = re.compile(r"""["'](?:gh["']\s*,\s*["'])?pr["']\s*,\s*["']create["']""")
#: The flag that carries a PR body — file first, so `--body` does not shadow `--body-file`.
BODY_FLAG = re.compile(r"(?<![\w-])(--body-file|--body|-b)(?!=)")
#: The flag that carries a commit message.
MSG_FLAG = re.compile(r"(?<![\w-])(--message|-m|-F|--file)(?!=)")
BODY_FLAGS = ("--body-file", "--body", "-b")
MSG_FLAGS = ("--message", "-m", "-F", "--file")
#: Shell keywords and Python call openings a real invocation may sit behind.
INVOKE_PREFIXES = ("if ", "if ! ", "then ", "do ", "sudo ", "sudo -E ", "! ", "exec ",
                   "subprocess.run(", "subprocess.check_call(", "subprocess.check_output(", "run(")
#: A shell separator an invocation may follow.
INVOKE_SEPARATORS = ("; ", "&& ", "|| ", "| ")


def producer_files(root: Path = REPO_ROOT) -> list[Path]:
    """Every file the repository owns that can run a commit or open a PR."""
    out = list(sorted((root / WORKFLOWS).glob("*.yml")))
    makefile = root / "Makefile"
    if makefile.exists():
        out.append(makefile)
    for pattern in ("*.sh", "*.py"):
        out += sorted((root / SCRIPTS).rglob(pattern))
    return out


def _commands(text: str) -> list[str]:
    """Logical shell commands: backslash-continued lines joined, every other line on its own."""
    out: list[str] = []
    buf = ""
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buf += stripped[:-1] + " "
            continue
        buf += stripped
        if buf.strip():
            out.append(buf.strip())
        buf = ""
    if buf.strip():
        out.append(buf.strip())
    return out


def _normalize(cmd: str) -> str:
    """A shell-ish view of a command: the Python argv separators and the brackets flattened."""
    s = re.sub(r"""["'],\s*["']""", " ", cmd)
    for ch in ("[", "]", '"', "'"):
        s = s.replace(ch, " ")
    return s


def _invokes(cmd: str, pattern: re.Pattern) -> bool:
    """Does `cmd` INVOKE this program, rather than merely mention it in prose?

    The invocation must stand at the start of a command — after a shell keyword, a call opening, or
    a separator — so a docstring that names the command mid-sentence is not read as a producer.
    """
    def at_start(s: str) -> bool:
        s = s.lstrip()
        for prefix in INVOKE_PREFIXES:
            if s.startswith(prefix):
                s = s[len(prefix):].lstrip()
        return bool(pattern.match(s))

    if at_start(cmd):
        return True
    for sep in INVOKE_SEPARATORS:
        idx = cmd.find(sep)
        while idx != -1:
            if at_start(cmd[idx + len(sep):]):
                return True
            idx = cmd.find(sep, idx + 1)
    return False


def _shell_value(cmd: str, m: re.Match) -> str | None:
    """The value after a flag in a shell command: a quoted span (spaces included), or one token."""
    rest = cmd[m.end():].lstrip()
    if not rest:
        return None
    if rest[0] in "\"'":
        end = rest.find(rest[0], 1)
        return rest[1:end] if end != -1 else rest[1:]
    return rest.split()[0]


def _shell_values(cmd: str, flag_re: re.Pattern) -> list[str]:
    out = []
    for m in flag_re.finditer(cmd):
        value = _shell_value(cmd, m)
        if value is not None:
            out.append(value)
    return out


def _py_values(chunk: str, flags: tuple[str, ...]) -> list[str]:
    """The values after a flag in a Python argv list: `"--body", body` -> `body`."""
    out = []
    for name in flags:
        pattern = re.compile(rf"""(?<![\w-]){re.escape(name)}["']?\s*,\s*([^\s,\]\)]+)""")
        out += [m.group(1).strip("\"'") for m in pattern.finditer(chunk)]
    return out


def _py_chunks(text: str) -> list[str]:
    """The text up to each `]` — an argv list ends there, so a chunk is one call's arguments."""
    out: list[str] = []
    start = 0
    for m in re.finditer(r"\]", text):
        out.append(text[start:m.end()])
        start = m.end()
    return out


def _placeholder(value: str) -> bool:
    return value.strip().strip("\"'").strip().lower() in PLACEHOLDERS


def _body_of(message_parts: list[str]) -> bool:
    """A message carries a body when a SECOND real part is passed, or the message spans lines."""
    real = [p for p in message_parts if not _placeholder(p)]
    if len(real) >= 2:
        return True
    return any("\n" in p or "\\n" in p for p in real)


def _commit_finding(where: str, shown: str, parts: list[str]) -> dict | None:
    """The violation a commit's message parts are, or None when the message is complete."""
    if not parts:
        return {
            "key": f"commit-message/{where}:{shown[:40]}",
            "title": f"ci: {where} runs a commit with no message",
            "evidence": (
                f"`{where}` runs `{shown[:160]}` and passes no message, so the commit lands empty "
                f"(or git opens an editor that does not exist in CI). AGENTS.md requires a typed "
                f"Conventional Commit subject plus a body stating the issue, the fix and the benefit."
            ),
            "where": where,
        }
    subject = parts[0]
    if _placeholder(subject):
        return {
            "key": f"commit-message-placeholder/{where}:{shown[:40]}",
            "title": f"ci: {where} commits a placeholder message (`{subject}`)",
            "evidence": (
                f"`{where}` runs `{shown[:160]}` with the subject `{subject}`, which says nothing "
                f"about what changed. A placeholder subject is the same defect as an empty one for "
                f"anyone reading the history."
            ),
            "where": where,
        }
    if not CONVENTIONAL.match(subject):
        return {
            "key": f"commit-message-subject/{where}:{shown[:40]}",
            "title": f"ci: {where} commits a subject that is not a typed Conventional Commit",
            "evidence": (
                f"`{where}` runs `{shown[:160]}` with the subject `{subject}`; AGENTS.md requires "
                f"`type(scope): summary` so the history is machine-readable and a reviewer sees the "
                f"intent before the diff."
            ),
            "where": where,
        }
    if not _body_of(parts):
        return {
            "key": f"commit-message-body/{where}:{shown[:40]}",
            "title": f"ci: {where} commits a subject with no body",
            "evidence": (
                f"`{where}` runs `{shown[:160]}` with a single message part and no body. A reader of "
                f"that commit learns the what, never the issue it answers, the mechanism that fixes "
                f"it, or the benefit — AGENTS.md requires a body carrying all three plus the "
                f"technical extension."
            ),
            "where": where,
        }
    return None


def _pr_finding(where: str, shown: str, values: list[str]) -> dict | None:
    """The violation a PR-open's body is, or None when a real body is passed."""
    if not values:
        return {
            "key": f"pr-body-missing/{where}:{shown[:40]}",
            "title": f"ci: {where} opens a PR with no body",
            "evidence": (
                f"`{where}` runs `{shown[:200]}` and passes no body, so the PR opens with an empty "
                f"description. AGENTS.md requires the body to state the issue, the fix and the "
                f"benefit, plus the technical extension, and to end with `closes #<issue>`."
            ),
            "where": where,
        }
    if _placeholder(values[0]):
        return {
            "key": f"pr-body-placeholder/{where}:{shown[:40]}",
            "title": f"ci: {where} opens a PR with a placeholder body (`{values[0]}`)",
            "evidence": (
                f"`{where}` runs `{shown[:200]}` with a body of `{values[0]}`, which tells a "
                f"reviewer nothing about the issue, the fix or the benefit."
            ),
            "where": where,
        }
    return None


def check_producers(root: Path) -> list[dict]:
    """Every commit and PR open a producer in this repository runs carries a real message/body."""
    out: list[dict] = []
    for path in producer_files(root):
        where = str(path.relative_to(root))
        text = path.read_text()
        if path.suffix == ".py":
            for chunk in _py_chunks(text):
                if PY_GIT_COMMIT.search(chunk):
                    finding = _commit_finding(where, chunk.strip()[-160:], _py_values(chunk, MSG_FLAGS))
                    if finding:
                        out.append(finding)
                if PY_PR_CREATE.search(chunk):
                    finding = _pr_finding(where, chunk.strip()[-200:], _py_values(chunk, BODY_FLAGS))
                    if finding:
                        out.append(finding)
            continue
        for cmd in _commands(text):
            if _invokes(cmd, GIT_COMMIT):
                finding = _commit_finding(where, cmd, _shell_values(cmd, MSG_FLAG))
                if finding:
                    out.append(finding)
            if _invokes(_normalize(cmd), GH_PR_CREATE):
                finding = _pr_finding(where, cmd, _shell_values(cmd, BODY_FLAG))
                if finding:
                    out.append(finding)
    return out


def check_agents_mandate(root: Path) -> list[dict]:
    """AGENTS.md carries the mandate section AND the closing rule, so neither is deleted silently."""
    text = (root / AGENTS).read_text() if (root / AGENTS).exists() else ""
    out: list[dict] = []
    if AGENTS_MANDATE not in text:
        out.append({
            "key": "agents-mandate/agents-md",
            "title": "ci: AGENTS.md no longer carries the PR/commit message mandate",
            "evidence": (
                f"`{AGENTS}` does not contain the heading `{AGENTS_MANDATE}`. That section states what "
                f"every commit message and PR body must carry — the issue, the fix, the benefit and the "
                f"technical extension. A rule that can be deleted by accident is not a rule, so its "
                f"presence is checked (issue #313)."
            ),
            "where": AGENTS,
        })
    if AGENTS_CLOSING_RULE not in text:
        out.append({
            "key": "agents-closing-rule/agents-md",
            "title": "ci: AGENTS.md no longer states that a PR closes the issue it implements",
            "evidence": (
                f"`{AGENTS}` does not contain `{AGENTS_CLOSING_RULE}`. A PR that implements an issue "
                f"must close it (`closes #<n>`); a partial implementation must not, and must name what "
                f"remains as a linked work item. Without the rule stated, a PR that closes nothing "
                f"passes review silently — 13 of the last 38 merged PRs did exactly that on `main` "
                f"(`4d999e3`), and #321 was closed by hand with no implementing PR while its defect "
                f"still reproduced. The rule cannot be deleted by an edit that leaves the code green "
                f"(issue #324)."
            ),
            "where": AGENTS,
        })
    return out


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def merge_base(root: Path, base: str, head: str) -> str | None:
    """`git merge-base <base> <head>` — the `main` the PR was cut from, or None when unreadable."""
    proc = _git(root, "merge-base", base, head)
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None


def agents_at(root: Path, sha: str) -> str | None:
    """`AGENTS.md` as it was at *sha*, read from the object store (not the working tree)."""
    proc = _git(root, "show", f"{sha}:{AGENTS}")
    return proc.stdout if proc.returncode == 0 else None


def _agents_line_finding(key: str, title: str, evidence: str, where: str) -> dict:
    return {"key": key, "title": title, "evidence": evidence, "where": where}


def is_bot_pr(root: Path, base: str, head: str) -> bool:
    """Whether the commits this PR adds are a bot leg's — every one authored by `BOT_EMAIL`.

    The `AGENTS:` line is the BOT contract (issue #792): a leg cites the rulebook it obeyed. A
    human PR is not held to it, so an all-human range is skipped rather than failed — otherwise
    every PR a person opens would go red for a rule stated nowhere they read. An empty range (a
    push to `main`, or `HEAD` == `base`) is not a bot PR.
    """
    proc = _git(root, "log", "--format=%ae", f"{base}..{head}")
    if proc.returncode != 0:
        return False
    authors = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return bool(authors) and all(author == BOT_EMAIL for author in authors)


def check_agents_line(body: str, root: Path = REPO_ROOT,
                      base: str = "origin/main", head: str = "HEAD") -> list[dict]:
    """A bot PR body carries `AGENTS:` with the merge-base sha and that sha's `AGENTS.md` counts."""
    if not is_bot_pr(root, base, head):
        return []
    out: list[dict] = []
    where = "pull request body"
    m = AGENTS_LINE.search(body or "")
    if not m:
        return [_agents_line_finding(
            "pr-agents-line-missing/pull-request",
            "ci: the PR body carries no `AGENTS:` line",
            f"The body states no `{AGENTS_LINE_SHAPE}` line, so a reviewer cannot tell which "
            f"`{AGENTS}` the work obeyed. `make bot-preflight` writes the line (first line of "
            f"`preflight.txt`); the PR body repeats it verbatim (issue #792).",
            where,
        )]
    sha, claimed_bytes, claimed_lines = m.group("sha"), int(m.group("bytes")), int(m.group("lines"))

    # The cited sha must be a `main` the work actually contains: an ancestor of BOTH the PR head and
    # the base. Comparing against the merge base alone made every `rebase-bot` rebase red the PR —
    # the merge base moves whenever `main` does, while the `AGENTS.md` the leg read is still a
    # perfectly good (and still reachable) rulebook. An ancestor is the rule the evidence supports.
    for label, ref in (("the PR head", head), (f"{base}", base)):
        if _git(root, "merge-base", "--is-ancestor", sha, ref).returncode != 0:
            want = merge_base(root, base, head) or "(unreadable)"
            return [_agents_line_finding(
                "pr-agents-line-sha/pull-request",
                "ci: the PR body cites an `AGENTS.md` the PR does not contain",
                f"The body's `AGENTS:` line names `{sha}`, but that commit is not an ancestor of "
                f"{label} (`git merge-base --is-ancestor {sha} {ref}` failed), so the rulebook it "
                f"cites is not one this branch contains. The current `git merge-base {base} {head}` "
                f"is `{want}` — re-run `make bot-preflight` and copy its line (issue #792).",
                where,
            )]

    text = agents_at(root, sha)
    if text is None:
        out.append(_agents_line_finding(
            "pr-agents-line-object/pull-request",
            f"ci: `{sha}` carries no readable `{AGENTS}`",
            f"The body's `AGENTS:` line names `{sha}`, but `git show {sha}:{AGENTS}` failed, so "
            f"the byte/line counts cannot be verified against the rulebook at that commit.",
            where,
        ))
        return out
    real_bytes, real_lines = len(text.encode("utf-8")), text.count("\n")
    if (claimed_bytes, claimed_lines) != (real_bytes, real_lines):
        out.append(_agents_line_finding(
            "pr-agents-line-size/pull-request",
            "ci: the PR body's `AGENTS:` counts do not match `AGENTS.md` at its sha",
            f"The body claims `{claimed_bytes}b {claimed_lines}l`, but `{AGENTS}` at `{sha}` is "
            f"`{real_bytes}b {real_lines}l`. A count that drifts from the sha means the line was "
            f"copied from somewhere other than that rulebook (issue #792).",
            where,
        ))
    return out


def read_pr_body(root: Path = REPO_ROOT, body: str | None = None, body_file: str | None = None,
                 pr: str | None = None, repo: str | None = None) -> tuple[str | None, str]:
    """The PR body to read, and where it came from — no `gh` call unless `--pr`/`--repo` ask for one.

    A push to `main` has no PR body; the static half of this gate still runs there, so "no body
    source" is a stated note rather than a failure. Every source that IS given must be readable: an
    unreadable file or an undefined `gh` is a failure, never a silent "no body".
    """
    if body is not None:
        return body, "--pr-body"
    if body_file:
        path = Path(body_file)
        if not path.is_file():
            raise RuntimeError(f"--pr-body-file {body_file} does not exist")
        return path.read_text(encoding="utf-8"), f"--pr-body-file {body_file}"
    env_file = os.environ.get("PR_BODY_FILE")
    if env_file:
        path = Path(env_file)
        if not path.is_file():
            raise RuntimeError(f"$PR_BODY_FILE {env_file} does not exist")
        return path.read_text(encoding="utf-8"), f"$PR_BODY_FILE {env_file}"
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).is_file():
        try:
            event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"$GITHUB_EVENT_PATH {event_path} is unreadable: {exc}") from exc
        pull = event.get("pull_request") if isinstance(event, dict) else None
        if isinstance(pull, dict) and pull.get("body") is not None:
            return pull["body"], f"$GITHUB_EVENT_PATH pull_request.body (#{pull.get('number', '?')})"
        return None, f"$GITHUB_EVENT_PATH {event_path} carries no pull_request.body"
    if pr and repo:
        proc = subprocess.run(["gh", "pr", "view", str(pr), "--repo", repo, "--json", "body",
                               "-q", ".body"], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"`gh pr view {pr} --repo {repo}` failed: "
                               f"{(proc.stderr or proc.stdout).strip()}")
        return proc.stdout, f"gh pr view {pr} --repo {repo}"
    return None, "no PR body source (a push to main has none, and neither --pr-body-file nor $PR_BODY_FILE was set)"


def findings(root: Path = REPO_ROOT, base: str = "origin/main", head: str = "HEAD",
             body: str | None = None) -> list[dict]:
    """Every violation: the producers, the AGENTS.md mandates, and the PR body's `AGENTS:` line."""
    out = check_producers(root) + check_agents_mandate(root)
    if body is not None:
        out += check_agents_line(body, root, base, head)
    return out


def render(items: list[dict]) -> str:
    if not items:
        return "[pr-hygiene] OK: every producer states the issue, the fix and the benefit"
    lines = [f"[pr-hygiene] {len(items)} violation(s)"]
    for f in items:
        lines += ["", f"- {f['title']}", f"  where: {f['where']}", f"  {f['evidence']}"]
    return "\n".join(lines)


def report(root: Path = REPO_ROOT, base: str = "origin/main", head: str = "HEAD",
           body: str | None = None, body_source: str = "none") -> str:
    """Every producer and the messages it passes — the human view of what the guard reads."""
    lines = ["[pr-hygiene] producers and their messages"]
    for path in producer_files(root):
        rel = str(path.relative_to(root))
        found: list[str] = []
        text = path.read_text()
        if path.suffix == ".py":
            for chunk in _py_chunks(text):
                if PY_GIT_COMMIT.search(chunk):
                    parts = _py_values(chunk, MSG_FLAGS)
                    found.append(f"    commit      parts={len(parts)} subject={parts[0] if parts else '(none)'}")
                if PY_PR_CREATE.search(chunk):
                    values = _py_values(chunk, BODY_FLAGS)
                    found.append(f"    pr open     body={values[0] if values else '(none)'}")
        else:
            for cmd in _commands(text):
                if _invokes(cmd, GIT_COMMIT):
                    parts = _shell_values(cmd, MSG_FLAG)
                    found.append(f"    commit      parts={len(parts)} subject={parts[0] if parts else '(none)'}")
                if _invokes(_normalize(cmd), GH_PR_CREATE):
                    values = _shell_values(cmd, BODY_FLAG)
                    found.append(f"    pr open     body={values[0] if values else '(none)'}")
        if found:
            lines.append(f"- {rel}")
            lines += found
    lines += ["", f"[pr-hygiene] PR body source: {body_source}"]
    if body is not None:
        agents_found = check_agents_line(body, root, base, head)
        if not is_bot_pr(root, base, head):
            lines.append("[pr-hygiene] AGENTS: line: not a bot range — skipped (a human PR is not held "
                         "to the bot contract)")
        else:
            verdict = "OK" if not agents_found else f"{len(agents_found)} finding(s)"
            lines.append(f"[pr-hygiene] AGENTS: line: {verdict}")
            for item in agents_found:
                lines.append(f"  {item['key']}: {item['title']}")
    else:
        lines.append("[pr-hygiene] AGENTS: line: no body to read (the static half decides)")
    lines += ["", render(findings(root, base, head, body))]
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="check_pr_hygiene", description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    for name in ("check", "report"):
        c = sub.add_parser(name)
        c.add_argument("--root", default=str(REPO_ROOT))
        c.add_argument("--base", default="origin/main",
                       help="the base the AGENTS: line is measured against")
        c.add_argument("--head", default="HEAD")
        c.add_argument("--pr-body", default=None, help="the PR body itself (tests, ad-hoc checks)")
        c.add_argument("--pr-body-file", default=None,
                       help="a file carrying the PR body, e.g. the implementer's pr-body.md")
        c.add_argument("--pr", default=None, help="read the body of this PR through `gh` (with --repo)")
        c.add_argument("--repo", default=None, help="owner/name for --pr")
    args = p.parse_args(argv)
    if not args.cmd:
        p.error("need a command: check | report")
    root = Path(args.root)
    try:
        body, source = read_pr_body(root, args.pr_body, args.pr_body_file, args.pr, args.repo)
    except RuntimeError as exc:
        print(f"[pr-hygiene] FAIL: {exc}", file=sys.stderr)
        return 2
    if args.cmd == "report":
        print(report(root, args.base, args.head, body, source))
        return 0
    print(f"[pr-hygiene] PR body: {source}")
    items = findings(root, args.base, args.head, body)
    print(render(items))
    return 1 if items else 0


if __name__ == "__main__":
    raise SystemExit(main())
