"""The PR/commit message-substance guard (issue #313) and the closing rule (issue #324).

A commit and a PR are read on their own, so a message that carries a subject and nothing else fails
the reviewer exactly as an empty one does. Every rule is tested on a fixture tree first — a bodiless
commit, a placeholder subject, a subject that is not a typed Conventional Commit, a PR opened with no
body or an empty one, an `AGENTS.md` that lost the mandate or the closing rule, and the Python argv
form the repo's `_gh` helper uses — and then the guard is run over THIS repository, because a
convention the repo itself violates is not a convention.

The exit code matters as much as the rules: `make check-pr-hygiene` runs inside the `ci-unit` job, so
`main(["check"])` must return non-zero on a violation and 0 on this tree.

NO-SKIP POLICY: a missing prerequisite is a LOUD FAILURE, never a skip.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_pr_hygiene as cph  # noqa: E402

#: An AGENTS.md that carries the mandate — the baseline every fixture starts from. It carries BOTH
#: required texts: the message mandate and the closing rule, so a fixture that drops either is the
#: one thing a test breaks.
AGENTS_OK = ("# Agents\n\n" + cph.AGENTS_MANDATE + "\n\n" + cph.AGENTS_CLOSING_RULE
             + "\n\nThe body of the mandate.\n")
#: The three producers whose messages this change gives a body.
PRODUCERS = (".github/workflows/engine-bump.yml",
             ".github/workflows/issue-bot.yml",
             ".github/workflows/registry-sync.yml")


def _tree(tmp_path: Path, shell: str = "", py: str = "", agents: str | None = AGENTS_OK) -> Path:
    """A fixture repo with one shell producer, one Python producer and an AGENTS.md."""
    root = tmp_path / "repo"
    (root / cph.SCRIPTS).mkdir(parents=True, exist_ok=True)
    if shell:
        (root / cph.SCRIPTS / "a.sh").write_text(shell)
    if py:
        (root / cph.SCRIPTS / "a.py").write_text(py)
    if agents is not None:
        (root / cph.AGENTS).write_text(agents)
    return root


def _keys(root: Path) -> list[str]:
    return [f["key"].split("/")[0] for f in cph.findings(root)]


def test_a_bodiless_commit_is_a_violation(tmp_path: Path):
    """A subject with no second message part is a commit a reader cannot learn from."""

    # Given a producer that commits a typed subject and nothing else
    root = _tree(tmp_path, shell='git commit -m "chore(engine): bump x to v1"\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  the missing body is a violation
    assert "commit-message-body" in keys


def test_a_placeholder_subject_is_a_violation(tmp_path: Path):
    """`-m update -m body` is as empty as `-m update` — the subject says nothing."""

    # Given a producer whose subject is a placeholder
    root = _tree(tmp_path, shell='git commit -m "update" -m "a real body"\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  the placeholder subject is a violation
    assert "commit-message-placeholder" in keys


def test_a_subject_that_is_not_conventional_is_a_violation(tmp_path: Path):
    """The subject must be a typed Conventional Commit, so history stays machine-readable."""

    # Given a producer whose subject has no type or scope
    root = _tree(tmp_path, shell='git commit -m "bumped things" -m "a real body"\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  the untyped subject is a violation
    assert "commit-message-subject" in keys


def test_a_subject_and_body_is_accepted(tmp_path: Path):
    """The shape AGENTS.md mandates passes: a typed subject plus a real body."""

    # Given a producer that passes a typed subject and a body variable
    root = _tree(tmp_path, shell='git commit -m "chore(engine): bump x" -m "$msg"\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  nothing is reported
    assert keys == []


def test_a_commit_with_no_message_at_all_is_a_violation(tmp_path: Path):
    """A commit that passes no `-m` lands empty (or opens an editor that does not exist in CI)."""

    # Given a producer that commits without a message
    root = _tree(tmp_path, shell='git commit --allow-empty\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  the missing message is a violation
    assert "commit-message" in keys


def test_a_pr_with_no_body_is_a_violation(tmp_path: Path):
    """A PR opened with no `--body` has an empty description a reviewer cannot use."""

    # Given a producer that opens a PR with a title only
    root = _tree(tmp_path, shell='gh pr create --base main --title "chore: thing"\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  the missing body is a violation
    assert "pr-body-missing" in keys


def test_an_empty_pr_body_is_a_violation(tmp_path: Path):
    """`--body ""` and `--body "-"` are placeholders, not descriptions."""

    # Given a producer that opens a PR with an empty body
    root = _tree(tmp_path,
                 shell='gh pr create --base main --title "chore: thing" --body ""\n'
                       'gh pr create --base main --title "chore: other" --body "-"\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  both placeholder bodies are violations
    assert keys.count("pr-body-placeholder") == 2


def test_a_body_variable_or_file_is_accepted(tmp_path: Path):
    """A body passed through a variable or a file is a real body — the guard does not read its text."""

    # Given producers that pass a body variable and a body file
    root = _tree(tmp_path,
                 shell='gh pr create --base main --title "chore: thing" --body "$body"\n'
                       'gh pr create --base main --title "chore: other" --body-file body.md\n')

    # When  the guard reads it
    keys = _keys(root)

    # Then  nothing is reported
    assert keys == []


def test_the_python_argv_form_is_covered(tmp_path: Path):
    """The repo's `_gh` helper builds an argv list, so the guard reads that form too."""

    # Given a Python producer that opens a PR without a body
    bad = _tree(tmp_path / "bad", py='out = _gh(gh, ["pr", "create", "--title", title])\n')

    # When  the guard reads it
    bad_keys = _keys(bad)

    # And   a Python producer that passes a body variable
    good = _tree(tmp_path / "good",
                 py='out = _gh(gh, ["pr", "create", "--title", title, "--body", body])\n')

    # Then  the missing body is a violation and the variable is accepted
    assert "pr-body-missing" in bad_keys
    assert _keys(good) == []


def test_a_missing_agents_mandate_is_a_violation(tmp_path: Path):
    """The mandate cannot be deleted silently — its heading is checked."""

    # Given an AGENTS.md without the mandate section
    root = _tree(tmp_path, agents="# Agents\n\nNo mandate here.\n")

    # When  the guard reads it
    keys = _keys(root)

    # Then  the missing mandate is a violation
    assert "agents-mandate" in keys


def test_a_missing_closing_rule_is_a_violation(tmp_path: Path):
    """A PR must close the issue it implements — the closing rule cannot be deleted silently."""

    # Given an AGENTS.md that carries the mandate but NOT the closing rule
    agents = "# Agents\n\n" + cph.AGENTS_MANDATE + "\n\nThe body of the mandate.\n"
    root = _tree(tmp_path, agents=agents)

    # When  the guard reads it
    items = cph.findings(root)
    keys = _keys(root)

    # Then  the closing rule is reported as its OWN finding — not the message mandate
    assert "agents-closing-rule" in keys
    assert "agents-mandate" not in keys
    assert "MUST close it" in cph.render(items)


def test_agents_mandate_passes_when_the_closing_rule_is_present(tmp_path: Path):
    """Both required texts present → no AGENTS.md finding at all."""

    # Given the baseline AGENTS.md, which carries the mandate AND the closing rule
    root = _tree(tmp_path)

    # When  the guard reads it
    keys = _keys(root)

    # Then  neither the mandate nor the closing rule is reported
    assert "agents-mandate" not in keys
    assert "agents-closing-rule" not in keys


def test_this_repository_carries_the_closing_rule():
    """AGENTS.md states the closing rule, so this repo's own PRs follow it."""

    # Given this repository's AGENTS.md
    text = (REPO / cph.AGENTS).read_text()

    # Then  the closing rule text is present, verbatim
    assert cph.AGENTS_CLOSING_RULE in text


def test_check_exits_non_zero_on_a_violation_and_zero_on_this_repo(tmp_path: Path):
    """`main(["check"])` is what `ci-unit` gates on."""

    # Given a fixture tree with a bodiless commit
    root = _tree(tmp_path, shell='git commit -m "chore(engine): bump x"\n')

    # When  the guard checks the fixture and this repository
    bad = cph.main(["check", "--root", str(root)])
    good = cph.main(["check", "--root", str(REPO)])

    # Then  the violation is non-zero and this tree is zero
    assert bad == 1
    assert good == 0


def test_this_repository_passes_its_own_guard():
    """Every producer in this repo passes: a convention the repo violates is not a convention."""

    # Given this repository
    # When  the guard reads it
    items = cph.findings(REPO)

    # Then  it reports no violation
    assert items == [], cph.render(items)


def test_this_repositorys_producers_state_the_issue_the_fix_and_the_benefit():
    """The commit each producer runs carries the three parts and the technical extension."""

    # Given the three producers that commit
    for rel in PRODUCERS:
        text = (REPO / rel).read_text()

        # When  its commit line is read
        commit_lines = [l for l in text.splitlines() if l.strip().startswith("git commit")]

        # Then  it passes a second message part, and the message names all four parts
        assert commit_lines, f"{rel} no longer commits"
        assert all('-m "$msg"' in l for l in commit_lines), rel
        for part in ("Issue:", "Fix:", "Benefit:", "Technical:"):
            assert part in text, f"{rel} does not state {part}"


# ---------------------------------------------------------------------------------------------
# The `AGENTS:` line a bot PR body carries (issue #792). Every case runs REAL git: the rule is a
# merge-base fact and a `git show <sha>:AGENTS.md` fact, so a stubbed git would prove nothing.
# ---------------------------------------------------------------------------------------------


def _git(cwd: Path, *args: str) -> str:
    """Run real git with an identity and return its stdout."""
    proc = subprocess.run(
        ["git", "-c", "user.name=Asimov Agent", "-c", "user.email=support@docondee.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=str(cwd), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr or proc.stdout}")
    return proc.stdout


def _history(tmp_path: Path) -> tuple[Path, str, str]:
    """A repo whose `origin/main` is one commit behind HEAD — the base and head shas it returns."""
    root = tmp_path / "gitrepo"
    root.mkdir()
    _git(tmp_path, "init", "-q", "-b", "main", str(root))
    (root / cph.AGENTS).write_text(AGENTS_OK, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "chore: the rulebook on main")
    base = _git(root, "rev-parse", "HEAD").strip()
    _git(root, "update-ref", "refs/remotes/origin/main", base)
    _git(root, "checkout", "-qb", "feat/x")
    (root / "change.py").write_text("print('the change')\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "feat: the change")
    return root, base, _git(root, "rev-parse", "HEAD").strip()


def test_a_human_authored_pr_is_not_held_to_the_agents_line(tmp_path: Path):
    """The `AGENTS:` line is the BOT contract: a person's PR must not go red for it."""

    # Given a branch whose added commits include one authored by Andy Holst
    root, base, _ = _history(tmp_path)
    (root / "human.py").write_text("print('a person edits this')\n", encoding="utf-8")
    _git(root, "add", "-A")
    subprocess.run(
        ["git", "-c", "user.name=Andy Holst", "-c", "user.email=andy.holst@protonmail.com",
         "-c", "commit.gpgsign=false", "commit", "-qm", "fix: a human commit"],
        cwd=str(root), check=True, capture_output=True, text=True,
    )

    # When  the guard reads a body with no AGENTS: line
    keys = _keys_with_body(root, _body(None))

    # Then  no agents-line finding is reported (every other rule still applies)
    assert [k for k in keys if k.startswith("pr-agents-line")] == []
    assert cph.check_agents_line(_body(None), root) == []
    assert cph.is_bot_pr(root, "origin/main", "HEAD") is False


def test_a_bot_range_is_held_to_the_agents_line(tmp_path: Path):
    """Every commit authored by the bot identity is a bot PR, and it must cite the rulebook."""

    # Given a branch whose added commits are all authored by Asimov Agent
    root, base, _ = _history(tmp_path)

    # When  its body carries no AGENTS: line
    keys = _keys_with_body(root, _body(None))

    # Then  it is a bot range and the missing line is a finding
    assert cph.is_bot_pr(root, "origin/main", "HEAD") is True
    assert "pr-agents-line-missing" in keys


def _line(sha: str, text: str = AGENTS_OK) -> str:
    return f"AGENTS: {sha} {len(text.encode())}b {text.count(chr(10))}l"


def _body(line: str | None) -> str:
    parts = ["Issue: #792 — a leg works from a stale tree.",
             "Fix: the preflight fetches and refuses.",
             "Benefit: the PR states the rulebook it obeyed.",
             "Technical: `scripts/bot_preflight.py`, `scripts/check_pr_hygiene.py`."]
    if line:
        parts.append(line)
    return "\n\n".join(parts) + "\n"


def _keys_with_body(root: Path, body: str | None, base: str = "origin/main") -> list[str]:
    return [f["key"].split("/")[0] for f in cph.findings(root, base, "HEAD", body)]


def test_a_pr_body_with_the_matching_agents_line_passes(tmp_path: Path):
    """The merge base's sha with that sha's `AGENTS.md` counts is what the rule asks for."""

    # Given a PR body carrying the AGENTS: line for the merge base
    root, base, _ = _history(tmp_path)
    body = _body(_line(base))

    # When  the guard reads it
    keys = _keys_with_body(root, body)

    # Then  no agents-line finding is reported
    assert [k for k in keys if k.startswith("pr-agents-line")] == []
    assert cph.check_agents_line(body, root) == []


def test_a_pr_body_without_the_agents_line_is_a_violation(tmp_path: Path):
    """A body that states the issue, the fix, the benefit and the technical and NOT the rulebook."""

    # Given a complete-looking body with no AGENTS: line
    root, _, _ = _history(tmp_path)

    # When  the guard reads it
    found = cph.check_agents_line(_body(None), root)

    # Then  it reports the missing line and says what the shape is
    assert [f["key"] for f in found] == ["pr-agents-line-missing/pull-request"]
    assert "AGENTS:" in found[0]["evidence"]


def test_a_pr_body_whose_agents_sha_the_pr_does_not_contain_is_a_violation(tmp_path: Path):
    """A sha the branch does not contain is the drift this rule exists to catch."""

    # Given a body whose AGENTS: sha is a commit this branch does not contain
    root, base, head = _history(tmp_path)
    body = _body(_line("0" * 40))

    # When  the guard reads it
    found = cph.check_agents_line(body, root)

    # Then  it names the sha and says it is not an ancestor of the branch
    assert "pr-agents-line-sha/pull-request" in [f["key"] for f in found]
    evidence = next(f["evidence"] for f in found if f["key"].startswith("pr-agents-line-sha"))
    assert "0" * 40 in evidence and base in evidence
    assert head != base


def test_a_pr_body_whose_agents_sha_is_an_older_main_passes(tmp_path: Path):
    """`rebase-bot` moves the merge base; the rulebook the leg read is still one main contained."""

    # Given a repo whose history has an older main commit, and a branch cut from a later one
    root = tmp_path / "gitrepo"
    root.mkdir()
    _git(tmp_path, "init", "-q", "-b", "main", str(root))
    (root / cph.AGENTS).write_text(AGENTS_OK, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "chore: the earlier rulebook")
    older = _git(root, "rev-parse", "HEAD").strip()
    (root / cph.AGENTS).write_text(AGENTS_OK + "\n## A later rule\n\nText.\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "docs: the later rulebook")
    _git(root, "update-ref", "refs/remotes/origin/main", _git(root, "rev-parse", "HEAD").strip())
    _git(root, "checkout", "-qb", "feat/x")
    (root / "change.py").write_text("print('the change')\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "feat: the change")

    # When  the body cites the older main commit, whose AGENTS.md the leg really read
    body = _body(_line(older))

    # Then  it passes: that commit is an ancestor of both the branch and origin/main
    assert [f["key"] for f in cph.check_agents_line(body, root)] == []
    assert cph.is_bot_pr(root, "origin/main", "HEAD") is True


def test_a_pr_body_whose_agents_counts_are_wrong_is_a_violation(tmp_path: Path):
    """The sha is right and the counts are not: the line was not copied from that rulebook."""

    # Given the merge base's sha with byte and line counts that are not AGENTS.md's
    root, base, _ = _history(tmp_path)
    body = _body(f"AGENTS: {base} 1b 1l")

    # When  the guard reads it
    found = cph.check_agents_line(body, root)

    # Then  it names the field and the real values from that sha's AGENTS.md
    keys = [f["key"] for f in found]
    assert keys == ["pr-agents-line-size/pull-request"]
    assert f"{len(AGENTS_OK.encode())}b" in found[0]["evidence"]


def test_a_non_bot_merge_commit_does_not_hide_a_bot_range(tmp_path: Path):
    """CI checks out `refs/pull/N/merge`, whose merge commit the merger authored — not the bot.

    Counting that merge commit as an author made `is_bot_pr()` false on every `pull_request` run,
    so `check_agents_line()` returned no finding and a bot PR with no `AGENTS:` line went green.
    """

    # Given a bot branch, a moved main, and a human-authored merge of main into the branch
    root, base, _ = _history(tmp_path)
    _git(root, "checkout", "-q", "main")
    (root / "later.py").write_text("print('main moves on')\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "feat: main moves on")
    _git(root, "checkout", "-q", "feat/x")
    subprocess.run(
        ["git", "-c", "user.name=Andy Holst", "-c", "user.email=andy.holst@protonmail.com",
         "-c", "commit.gpgsign=false", "merge", "--no-ff", "-m", "Merge main into feat/x", "main"],
        cwd=str(root), check=True, capture_output=True, text=True,
    )
    merge_head = _git(root, "rev-parse", "HEAD").strip()
    authors = _git(root, "log", "--format=%ae", f"origin/main..{merge_head}").split()

    # When  the guard reads a body with no AGENTS: line against that merge commit
    keys = [f["key"].split("/")[0] for f in cph.findings(root, "origin/main", merge_head, _body(None))]

    # Then  the human merge commit is in the range, yet the range is still the bot's and the
    #       missing line is still a finding
    assert "andy.holst@protonmail.com" in authors
    assert cph.is_bot_pr(root, "origin/main", merge_head) is True
    assert "pr-agents-line-missing" in keys
    assert base != merge_head


def test_the_pr_body_is_read_from_the_github_event_without_network(tmp_path: Path, monkeypatch):
    """`ci-unit` gets the body from the event JSON it was already given — no `gh`, no network."""

    # Given a GitHub event carrying pull_request.body with the right line
    root, base, _ = _history(tmp_path)
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {"number": 900, "body": _body(_line(base))}}),
                     encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.delenv("PR_BODY_FILE", raising=False)

    # When  the guard resolves the body
    body, source = cph.read_pr_body(root)

    # Then  it read the event's body and the rule passes on it
    assert source.startswith("$GITHUB_EVENT_PATH") and "pull_request.body" in source
    assert body is not None and _line(base) in body
    assert cph.main(["check", "--root", str(root)]) == 0


def test_with_no_pr_body_the_static_half_still_decides(tmp_path: Path, monkeypatch, capsys):
    """A push to `main` has no PR body: the note is printed and the exit code stays the static half's."""

    # Given no body source at all
    root, _, _ = _history(tmp_path)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    monkeypatch.delenv("PR_BODY_FILE", raising=False)

    # When  the guard runs against a clean tree
    rc = cph.main(["check", "--root", str(root)])

    # Then  it says it read no body, reports no agents-line finding, and exits 0
    out = capsys.readouterr()
    assert rc == 0
    assert "no PR body source" in out.out
    assert "pr-agents-line" not in out.out


def test_an_unreadable_pr_body_file_fails_loudly(tmp_path: Path, capsys):
    """A body source that IS given must be readable — never a silent "no body to check"."""

    # Given a --pr-body-file that does not exist
    root, _, _ = _history(tmp_path)

    # When  the guard runs with it
    rc = cph.main(["check", "--root", str(root), "--pr-body-file", str(tmp_path / "gone.md")])

    # Then  it exits 2 and names the file
    out = capsys.readouterr()
    assert rc == 2
    assert "does not exist" in out.err


def test_a_pr_body_file_is_the_implementers_pr_body(tmp_path: Path, monkeypatch):
    """`$PR_BODY_FILE` is how the implementer's `pr-body.md` is checked BEFORE the PR opens."""

    # Given the implementer's pr-body.md carrying a stale line
    root, base, _ = _history(tmp_path)
    body_file = tmp_path / "pr-body.md"
    body_file.write_text(_body(f"AGENTS: {base} 1b 1l"), encoding="utf-8")
    monkeypatch.setenv("PR_BODY_FILE", str(body_file))
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    # When  the guard runs with no PR= at all
    rc = cph.main(["check", "--root", str(root)])

    # Then  it fails on the counts, naming the file it read
    assert rc == 1
