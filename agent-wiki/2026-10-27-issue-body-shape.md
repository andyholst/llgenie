# 2026-10-27 — every issue states the goal, then the technical solution

Issue: [#745](https://github.com/asimov-agent/llgenie/issues/745)
OpenSpec: `openspec/changes/issue-body-shape`

## What was wrong

Seven producers filed issues, and each invented its own body: `security_issues.body_for` wrote
`**Advisory:** … ### Suggested action`, `code_review.issue_body` wrote an evidence blob plus
`- found by:`, the run-failure reactor wrote a paragraph and a log tail, `engine_skill_gap` wrote
`## Evidence / ## Why it matters / ## What to do (one of)`, `registry_change_issue` wrote
`## What changed / ## What this implies`, `architecture_bot` wrote one-line
`Issue: / Fix: / Benefit: / Technical:` paragraphs, and `queued_run_alarm` pasted the run report.
A PR body has been gated on `Issue: / Fix: / Benefit: / Technical:` since #313; an issue body was
gated on nothing, so the artifact an implementer starts from was the one nobody had to explain.

## What changed

- **`scripts/issue_body.py`** — the ONE renderer. `render(problem, why, how, benefit, acceptance,
  technical, not_covered=None, marker=None)` emits `## Problem`, `## Why it matters`,
  `## How we fix it`, `## Benefit`, `## Acceptance criteria` (each criterion a `- [ ]` item),
  optional `## Not covered`, then `## Technical` last. The producer's dedupe marker is the body's
  first line, byte for byte. `missing()` reports every defect (absent, out of order, duplicated,
  `Technical` not last, `Not covered` misplaced, acceptance criteria with no checkbox), and
  `section_body()` returns one section's text for a caller that needs it.
- **All seven producers render through it** — `security_issues`, `code_review`,
  `run_failure_reactor`, `engine_skill_gap`, `registry_change_issue`, `architecture_bot`,
  `queued_run_alarm`. `code_review`, `run_failure_reactor` and `engine_skill_gap` import the
  renderer as `render_body` because their own function is named `issue_body` — the published name is
  kept, no caller changed.
- **`scripts/check_issue_body.py`** + `make check-issue-bodies` / `make issue-bodies-report`, wired
  into `ci-unit` and classified in `issue_bot_gates.py` (deferred: `FAST_GATES` is the fixed
  six-gate list #475 pins, and widening it is that issue's follow-up). It fails on a producer that hand-builds a
  body (no renderer call, or a quoted `## ` heading of its own), on `AGENTS.md` losing the section,
  on an issue skill that stopped stating the shape, and on a renderer whose own output its own
  checker rejects.
- **AGENTS.md** — new MANDATORY section with the six-section shape, the PR-body mapping
  (`Problem`↔`Issue:`, `How we fix it`↔`Fix:`, `Benefit`↔`Benefit:`, `Technical`↔`Technical:`), the
  producer roster and the gate.
- **`.hermes/skills/issue-triage` + `issue-refiner`** — `REFINED:` / `RESTATED:` carry the same six
  sections, so the two legs that read human-written issues enforce the shape on issues no script
  wrote.

## Decisions

- **Acceptance criteria are a section, not a list inside `## Technical`.** The shape a producer
  writes and the shape a reviewer ticks have to be the same one; a criterion that is not a `- [ ]`
  item is not a criterion, and `missing()` says so.
- **Defaults, then `ValueError`.** `problem`/`why`/`benefit`/`how`/`acceptance`/`technical` default to
  empty so a caller that forgets one gets "`benefit` is required …" instead of a bare `TypeError`.
- **A prose mention is not a second shape.** The gate flags a quoted `"## Problem"` literal (how a
  hand-built body spells it), not a backticked `` `## Technical` `` inside a sentence.
- **`Not covered` stays optional but positional.** It is allowed anywhere between `## Benefit` and
  `## Technical`, and each item names the issue it was filed as (AGENTS.md: out-of-scope work is its
  own linked issue).

## Verified

- `tests/test_issue_body.py` (9): section order with `Technical` last, a missing section named,
  `Technical` moved to the front refused, `Not covered` before `Technical`, acceptance criteria
  without a checkbox refused, `render` refusing each missing field, the security marker first line +
  `MARKER_RE` round-trip, and all five scripted producers rendering tickable criteria.
- `tests/test_check_issue_body.py` (5): the real tree passes; a hand-built producer named; a lost
  AGENTS.md section named; a skill that dropped `## Acceptance criteria` named; renderer/checker agree.
- Updated in place (the rule moved, the tests still assert behaviour): `tests/test_security_issues.py`
  (the body's fragments and section order), `tests/test_architecture_bot.py` (the six sections on the
  ISSUE body, the four labelled parts on the PR body).
- Gates: `make lint check-wiring check-docs check-agent-skills check-issue-bodies check-workflows
  check-pr-hygiene issue-bot-gates-check` green; `make test-unit` green; `make openspec-validate
  NAME=issue-body-shape` passes.

## Status

Implemented on `feat/issue-body-shape`; the issues already open are not rewritten by this change —
the refiner restates one at a time, when it touches them.

## Follow-up (`daf1e6b`)

The queued-run alarm was the one producer whose evidence is a pasted log rather than a field list, and
the first version handed that already-fenced report to the renderer as three separate technical items,
so the filed body showed a fence colliding with its own fence. `_technical()` now emits a multi-line
item verbatim (one bullet per fact, a block kept as a block), `queued_run_alarm` passes the caller's
report as that one item, and `tests/test_queued_run_alarm.py` asserts the filed body's headings out of
the recorded `issue create` argv instead of trusting the call.
