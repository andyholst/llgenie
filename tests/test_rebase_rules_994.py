"""#994 pins: the rebase lane's SOUL and skill state rules 1 and 2 verbatim, cited to #994.

These are content checks, not counts: a lane that stops announcing before a rebase (rule 1) or stops
rebasing onto the fresh upstream main (rule 2) reds its own gate, and a lane that rewords them so the issue
can no longer be verified reds it too. The probes are the exact verbatim strings from issue #994.
"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
SOUL = REPO / "agents/llgenie-pr-merge-conflict/SOUL.md"
SKILL = REPO / "agents/llgenie-pr-merge-conflict/skills/llgenie-pr-rebase/SKILL.md"

RULE1 = "must always communicate with the other llgenie bots before rebasing an ongoing PR"
RULE2 = "keep their ongoing PR rebased onto the latest fetched `asimov-agent/llgenie` `main`"


def test_rule1_is_verbatim_in_the_lane_soul():
    assert SOUL.is_file(), f"{SOUL} missing"
    assert RULE1 in SOUL.read_text(encoding="utf-8")


def test_rule1_is_verbatim_in_the_lane_skill():
    assert SKILL.is_file(), f"{SKILL} missing"
    assert RULE1 in SKILL.read_text(encoding="utf-8")


def test_rule2_is_verbatim_in_the_lane_soul():
    assert RULE2 in SOUL.read_text(encoding="utf-8")


def test_both_rules_cite_the_issue_so_the_source_of_truth_is_named():
    soul = SOUL.read_text(encoding="utf-8")
    skill = SKILL.read_text(encoding="utf-8")
    assert "#994" in soul, "SOUL.md must cite #994"
    assert "#994" in skill, "SKILL.md must cite #994"
