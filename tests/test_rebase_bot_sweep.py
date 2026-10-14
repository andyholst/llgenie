"""The rebase bot: which PR it picks, and what it does to that PR (issue #246).

Two halves, both real code under test:

  * the SWEEP (scripts/rebase_bot_sweep.py) decides which ONE PR needs rebasing, driven through a
    fake `gh` that records argv, so the assertions are about the exact requests it makes;
  * the ACTOR (scripts/rebase_bot.sh) is driven against a real scratch git repository with two
    conflicting branches and a stub agent, so the rebase, the conflict hand-off, the structural
    gates and the force-with-lease push are exercised for real — only the LLM is a stand-in.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import rebase_bot_sweep as rb  # noqa: E402

OWNER, NAME = "asimov-agent", "llgenie"


# ------------------------------------------------------------------------------------- sweep
def _fake_gh(tmp_path: Path, opts: dict | None = None):
    opts = opts or {}
    tmp_path.mkdir(parents=True, exist_ok=True)
    log = tmp_path / "gh.log"
    # the fixtures go to disk as JSON and the stub reads them: embedding json.dumps() inside
    # generated Python source writes `false`/`true` literals, which are not Python.
    (tmp_path / "search.json").write_text(json.dumps(opts.get("search", [])))
    (tmp_path / "prs.json").write_text(json.dumps(opts.get("prs", [])))
    (tmp_path / "checks.json").write_text(json.dumps(opts.get("checks_by_pr", {})))
    gh = tmp_path / "gh"
    gh.write_text(f'''#!{sys.executable}
import json, sys, pathlib
args = sys.argv[1:]
here = pathlib.Path(__file__).parent
with open({str(log)!r}, "a") as fh:
    fh.write(json.dumps(args) + "\\n")
if args[:2] == ["search", "prs"]:
    print((here / "search.json").read_text())
elif args[:2] == ["pr", "list"]:
    print((here / "prs.json").read_text())
elif args[:2] == ["pr", "checks"]:
    f = here / "checks.json"
    by_pr = json.loads(f.read_text()) if f.exists() else {{}}
    states = by_pr.get(args[2], [])
    print(json.dumps([{{"state": s}} for s in states]))
else:
    print("")
''')
    gh.chmod(0o755)
    return gh, log


def _pr(num, state="BEHIND", *, draft=False, head="andyholst", repo=None, base="main",
        created="2026-10-01T00:00:00Z", title=None):
    return {"number": num, "title": title or f"PR {num}", "isDraft": draft,
            "mergeStateStatus": state, "headRefName": f"feat/{num}",
            "headRepositoryOwner": {"login": head}, "createdAt": created, "baseRefName": base}


def _marker_today(num, today="2026-10-14"):
    return {"number": num, "comments": [{"body": f"rebased. <!-- rebase-bot: {today} -->"}]}


def test_the_sweep_picks_one_pr_and_states_a_reason_for_every_pass_over(tmp_path):
    gh, _log = _fake_gh(tmp_path, {"search": [], "prs": [
        _pr(1, "CLEAN", created="2026-09-01T00:00:00Z"),
        _pr(2, draft=True, created="2026-09-02T00:00:00Z"),
        _pr(3, "BEHIND", base="release/1", created="2026-09-03T00:00:00Z"),
        _pr(4, "DIRTY", created="2026-09-04T00:00:00Z"),
        _pr(5, "BEHIND", created="2026-09-05T00:00:00Z"),
    ]})
    res = rb.sweep(str(gh), f"{OWNER}/{NAME}", today="2026-10-14", own_fork="andyholst")
    assert res["action"] == "rebase" and res["pr"] == 4, res
    assert res["head_branch"] == "feat/4" and res["state"] == "DIRTY"
    joined = " | ".join(res["reasons"])
    assert "#1 is CLEAN" in joined and "#2 is a draft" in joined
    assert "#3 targets release/1" in joined


def test_a_pr_already_rebased_today_is_left_alone(tmp_path):
    """The marker comment is the record: no label needed, and no rebase loop."""
    gh, log = _fake_gh(tmp_path, {"search": [_marker_today(7)], "prs": [
        _pr(7, "BEHIND", created="2026-09-01T00:00:00Z"),
        _pr(8, "BEHIND", created="2026-09-02T00:00:00Z")]})
    res = rb.sweep(str(gh), f"{OWNER}/{NAME}", today="2026-10-14", own_fork="andyholst")
    assert res["pr"] == 8, res
    assert any("already rebased today" in r for r in res["reasons"])
    q = [c for c in [json.loads(l) for l in log.read_text().splitlines()] if c[:2] == ["search", "prs"]][0]
    assert "--commenter" in q and "--updated" in q and ">=2026-10-14" in q


def test_the_daily_cap_stops_the_bot(tmp_path, capsys):
    gh, log = _fake_gh(tmp_path, {"search": [_marker_today(n) for n in range(1, 6)], "prs": []})
    res = rb.sweep(str(gh), f"{OWNER}/{NAME}", today="2026-10-14")
    assert res["action"] == "cap" and res["pr"] is None
    assert "already rebased 5/5 PRs today" in res["reason"]
    assert not [c for c in [json.loads(l) for l in log.read_text().splitlines()] if c[:2] == ["pr", "list"]]


def test_a_fork_this_bot_cannot_push_to_is_skipped(tmp_path):
    gh, _log = _fake_gh(tmp_path, {"search": [], "prs": [
        _pr(9, "BEHIND", head="stranger", created="2026-09-01T00:00:00Z"),
        _pr(10, "BEHIND", head="andyholst", created="2026-09-02T00:00:00Z")]})
    res = rb.sweep(str(gh), f"{OWNER}/{NAME}", today="2026-10-14", own_fork="andyholst")
    assert res["pr"] == 10, res
    assert any("not pushable here" in r for r in res["reasons"])


def test_nothing_to_do_is_reported_as_none(tmp_path):
    gh, _log = _fake_gh(tmp_path, {"search": [], "prs": [_pr(1, "CLEAN")]})
    res = rb.sweep(str(gh), f"{OWNER}/{NAME}", today="2026-10-14", own_fork="andyholst")
    assert res["action"] == "none" and "no open PR needs rebasing" in res["reason"]


# ------------------------------------------------------------------------------------- actor
def _scratch_repo(tmp_path: Path):
    """A real repo with a conflicting branch and a bare `fork` remote standing in for the PR head."""
    work = tmp_path / "work"
    remote = tmp_path / "fork.git"
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}

    def git(*args, cwd=work):
        return subprocess.run(["git", *args], cwd=str(cwd), env=env,
                              capture_output=True, text=True, check=True)

    work.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)  # before any push
    git("init", "-q", "-b", "main")
    (work / "shared.txt").write_text("base\n")
    git("add", "-A"); git("commit", "-qm", "base")
    # the PR branch changes the same line as main will
    git("checkout", "-q", "-b", "feat/conflict")
    (work / "shared.txt").write_text("from the PR\n")
    git("add", "-A"); git("commit", "-qm", "the PR's change")
    git("push", "-q", str(remote), "feat/conflict")
    # main moves on the same line
    git("checkout", "-q", "main")
    (work / "shared.txt").write_text("from main\n")
    git("add", "-A"); git("commit", "-qm", "main moves")
    git("push", "-q", str(remote), "main")
    # both remotes point at the same bare repo: `origin` is where main lives, `fork` is the PR's
    # head repository (the actor must publish the branch THERE, not to origin)
    git("remote", "add", "origin", str(remote))
    git("remote", "add", "fork", str(remote))
    git("fetch", "-q", "origin")
    git("checkout", "-q", "main")
    return work, remote, env


def _run_actor(tmp_path, work, env, agent_cmd, dry="", gates="true"):
    return subprocess.run(
        [os.environ.get("BASH", "bash"), str(REPO / "scripts" / "rebase_bot.sh")],
        cwd=str(work), env={**env, "PR": "42", "HEAD_BRANCH": "feat/conflict",
                            "HEAD_REPO": "andyholst", "REPO": f"{OWNER}/{NAME}",
                            "AGENT_CMD": agent_cmd, "GATES": gates, "DRY": dry},
        capture_output=True, text=True, timeout=180)


def test_a_conflict_is_handed_to_the_agent_and_the_result_is_pushed_to_the_fork(tmp_path):
    """The whole point: a conflicting PR comes back onto main, resolved by the agent, published
    to the PR's own remote — with the lease, and without rerere replaying an old resolution."""
    work, remote, env = _scratch_repo(tmp_path)
    agent = tmp_path / "agent.sh"
    agent.write_text('#!/usr/bin/env bash\nset -e\ncat >/dev/null\n'
                     'printf "from main\\nfrom the PR\\n" > shared.txt\n'
                     'git add shared.txt\n')
    agent.chmod(0o755)

    r = _run_actor(tmp_path, work, env, str(agent))
    assert r.returncode == 0, r.stdout + r.stderr
    # the agent resolved it, both sides survived, and the branch was published to the fork
    assert "from main\nfrom the PR" in (work / "shared.txt").read_text()
    pushed = subprocess.run(["git", "--git-dir", str(remote), "show", "feat/conflict:shared.txt"],
                            capture_output=True, text=True, check=True).stdout
    assert "from main" in pushed and "from the PR" in pushed
    # and it never ran a merge: the branch is rebased, not merged (git's own "merge conflict"
    # message in the log is expected and is why this checks the COMMAND, not the word)
    assert "git merge" not in r.stdout.lower()
    assert "--no-ff" not in r.stdout and "merge --" not in r.stdout


def test_the_actor_uses_the_lease_never_a_plain_force(tmp_path):
    work, _remote, env = _scratch_repo(tmp_path)
    r = _run_actor(tmp_path, work, env, "true", dry="1", gates="make -n ci-unit")
    out = r.stdout
    assert "rerere.enabled=false" in out, out
    assert "--force-with-lease" in out, out
    assert "--force " not in out and "--force\n" not in out, "a plain --force must never appear"
    assert out.index("make -n ci-unit") < out.index("--force-with-lease"), "gates before the push"


def test_a_failing_agent_stops_the_run_without_pushing(tmp_path):
    work, remote, env = _scratch_repo(tmp_path)
    before = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "feat/conflict"],
                            capture_output=True, text=True, check=True).stdout.strip()
    r = _run_actor(tmp_path, work, env, "false")
    assert r.returncode != 0
    after = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "feat/conflict"],
                           capture_output=True, text=True, check=True).stdout.strip()
    assert before == after, "a failed resolution must not publish anything"


def test_it_does_not_rebase_while_the_pr_has_checks_in_flight(tmp_path):
    """A rebase would cancel the very run that is deciding the PR (and can race the fix-bot)."""
    gh, _log = _fake_gh(tmp_path, {"search": [], "checks_by_pr": {"1": ["PENDING"]},
                                   "prs": [_pr(1, "BEHIND", created="2026-09-01T00:00:00Z"),
                                           _pr(2, "BEHIND", created="2026-09-02T00:00:00Z")]})
    res = rb.sweep(str(gh), f"{OWNER}/{NAME}", today="2026-10-14", own_fork="andyholst")
    assert res["pr"] == 2, res
    assert any("checks in flight" in r for r in res["reasons"])


def test_a_red_pr_that_is_only_behind_is_left_to_the_fix_bot(tmp_path):
    """Division of labour: a rebase fixes staleness, not a failing test."""
    gh, _log = _fake_gh(tmp_path, {"search": [], "checks_by_pr": {"1": ["FAILURE"], "2": ["FAILURE"]},
                                   "prs": [_pr(1, "BEHIND", created="2026-09-01T00:00:00Z"),
                                           _pr(2, "DIRTY", created="2026-09-02T00:00:00Z")]})
    res = rb.sweep(str(gh), f"{OWNER}/{NAME}", today="2026-10-14", own_fork="andyholst")
    # the conflicted one is taken even though it is red: the rebase is the precondition
    assert res["pr"] == 2, res
    assert any("the fix-bot owns that" in r for r in res["reasons"])


def test_the_rebase_bot_gates_the_run_on_jev():
    """Every bot: the job does not start when the JEV engine is off. The rebase bot asked the agent
    to resolve conflicts with no JEV env at all, so its agent ran unsupervised (issue #238)."""
    from pathlib import Path
    repo = Path(__file__).resolve().parent.parent
    text = (repo / ".github/workflows/rebase-bot.yml").read_text()
    assert "NERVE_REQUIRE=1" in text, "the gate must be ARMED"
    assert text.index("JEV engine is active") < text.index("Rebase it (agent resolves"), \
        "the gate must run before the rebase"
    mk = (repo / "Makefile").read_text()
    recipe = mk[mk.index("rebase-bot-agent:"):mk.index("_rebase-bot-agent:")]
    assert "TYPESAFE_API_KEY" in recipe, "the key must reach the container at run time"
