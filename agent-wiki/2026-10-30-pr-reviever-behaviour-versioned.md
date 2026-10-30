# Reviewer lane behaviour is versioned: SOUL + the llgenie-pr-review skill (issue #1060)

What was out of the tree: `agents/llgenie-pr-reviever/SOUL.md` was **8912 b** against a live
SOUL of **11166 b**, and the lane's `software-development/llgenie-pr-review` skill existed only
on the host (repo: NONE) — so the procedure this lane's whole output depends on was unreviewable.

The drift was **judged, not copied** (a blind `cp` already cost this fleet once, `#923`/`#924`):
`diff -u` of the repo copy against live gives exactly **one hunk** (`@@ -67,6 +67,15 @@`) —
7 content lines added, **0 removed**, and **0 repo-only lines** (`diff | grep '^<'` empty), so
live is a strict superset. The added bytes are the `## Orchestration hand-off (#1010)` section:
the #1010 delegation/report-back loop (planner delegates → reviewer verdicts → reports
verdict+head back) and the #1015 clauses (rebase only on a real `CONFLICTING`, never on a
moved-but-clean base; fetch the real `asimov-agent/llgenie` main via `refs/remotes/live/main`
and cross-check the API, never the `origin/main` shadow). All 7 lines are this lane's own newer
rules; nothing in the repo copy was newer.

Versioned here, all byte-identical to live (`cmp -s` each):
`agents/llgenie-pr-reviever/SOUL.md` (11166 b) and
`agents/llgenie-pr-reviever/skills/software-development/llgenie-pr-review/` — `SKILL.md`
(100503 b, `version: 1.26.0`) plus `references/agent-profile-tree-review.md` (10882 b),
`references/board-sweep.md` (12040 b), `references/rebase-sweep.md` (8464 b). The layout
follows the tester lane's `agents/llgenie-tester/skills/llgenie-pr-testing/` shape;
`check_agent_skills.py`'s `## Inputs`/`## Output`/`## Rules` requirement applies to
`.hermes/skills/`, not to `agents/<lane>/skills/` (the tester's versioned SKILL carries none
either), so the live headings stand as they are.

`CHANGES.md` is deliberately **not** modified: `scripts/changes_index.py:11` states the index is
"rendered from those fragments by `make changes-index`; no change PR writes it" (issue #934 /
#1063). The fragment beside this note is the change's record; `make check-docs` passes with it
alone.

Gates: `sync-agent-profile PROFILE=llgenie-pr-reviever CHECK=1` → exit 0 ("8 file(s) … match
byte for byte"); `check_pr_authors` over `live/main..HEAD` OK; `make check-docs` exit 0. Opened
as an ordinary branch only after #919 put `agents/` on `main`, so this is a normal PR rather
than a stacked one.

Spec / issue / PR: issue #1060.
