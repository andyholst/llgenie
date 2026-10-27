# issue-body-shape — proposal

Issue: [#745](https://github.com/asimov-agent/llgenie/issues/745)
Related: [#738](https://github.com/asimov-agent/llgenie/issues/738) (the sibling "every pipeline explains itself" rule for the scan), [#717](https://github.com/asimov-agent/llgenie/issues/717) / [#716](https://github.com/asimov-agent/llgenie/issues/716) (the producers this touches first)

## Why

An issue is the root of this repository's pipeline: issue → feature branch → OpenSpec change → code →
PR → `closes #n`, and AGENTS.md says the work item's GOAL lives in the issue. The PR body is gated
(`check-pr-hygiene` refuses a body without `Issue: / Fix: / Benefit: / Technical:`), but an issue body
is gated by nothing at all, so the seven producers that file issues each invented their own shape:

- `scripts/security_issues.py::body_for` — marker, advisory/package/version/severity/run-link, then
  `### Suggested action` and `### Not covered`;
- `scripts/code_review.py::issue_body` — the evidence blob, `- found by:`, `- where:`, and "This is an
  analysis finding, not a fix";
- `scripts/run_failure_reactor.py::issue_body` — a paragraph, a field list, a log tail;
- `scripts/engine_skill_gap.py::issue_body` — `## Evidence`, `## Why it matters`, `## What to do (one of)`;
- `scripts/registry_change_issue.py::render` — `## What changed`, `## What this implies`, `## Not covered`;
- `scripts/architecture_bot.py::render_issue` — `Issue: / Fix: / Benefit: / Technical:` as one-line
  labelled paragraphs (the closest thing to the rule, and still not the rule);
- `scripts/queued_run_alarm.py::file_label_issue` — the run report, verbatim.

A reader who was not in the run that filed the issue cannot answer what is broken, why it is worth
fixing, or what the fix buys. The implementer (an agent leg) starts from that body; the PR's
`Benefit:` has to restate it; and the "issue / OpenSpec / code must agree" check compares three texts
that were never written in the same shape.

## What Changes

- **`scripts/issue_body.py`** (new) — the ONE renderer: `render(problem, why, how, benefit,
  acceptance, technical, not_covered=None, marker=None)`, producing `## Problem`, `## Why it matters`,
  `## How we fix it`, `## Benefit`, `## Acceptance criteria` (one `- [ ]` item per provable outcome),
  `## Not covered` (optional), `## Technical` — in that order, `## Technical` last, the producer's
  dedupe marker as the first line. `missing()` reports every defect in a given body, including an
  `## Acceptance criteria` section with no tickable item.
- **Every producer renders through it** — `security_issues`, `code_review`, `run_failure_reactor`,
  `engine_skill_gap`, `registry_change_issue`, `architecture_bot`, `queued_run_alarm`. Their markers,
  titles, labels and `gh` argv are untouched: a body is never restructured at the cost of the
  idempotence each producer relies on.
- **`scripts/check_issue_body.py`** (new) + `make check-issue-bodies` / `make issue-bodies-report` —
  the gate (mirroring `check_pr_hygiene.py`): a producer that builds a body without
  `issue_body.render`, a rendered body missing a section or out of order, an `AGENTS.md` that has lost
  the section, and an issue skill that no longer states the shape all fail it.
- **AGENTS.md** — a new MANDATORY section, "Every issue carries the problem, why, the fix and the
  benefit — then the technical solution", sitting beside the PR-body section it mirrors and stating the
  mapping (`Problem` ↔ `Issue:`, `How we fix it` ↔ `Fix:`, `Benefit` ↔ `Benefit:`, `Technical` ↔
  `Technical:`).
- **`.hermes/skills/issue-triage` and `.hermes/skills/issue-refiner`** — `REFINED:` / `RESTATED:` carry
  the same six sections (acceptance criteria tickable), so the two legs that read human-written issues
  enforce the shape on the issues no script wrote.
- **Wiring** — `check-issue-bodies` joins `make ci-unit` and is classified in
  `scripts/issue_bot_gates.py` (deferred, with its reason: `FAST_GATES` is the fixed six-gate list
  #475 pins), so a PR cannot land a producer that files an unreadable issue.
- **Docs** — `docs/BOTS.md` states the issue-body contract, `CHANGES.md` indexes the dated note in
  `agent-wiki/2026-10-27-issue-body-shape.md`.

## Not covered

- Retro-fitting open issues: bodies written from now on carry the shape; the ~40 open issues are
  restated one at a time by the refiner when it touches them (a bulk rewrite would destroy the review
  threads). Filed as its own work item if it is wanted as a sweep.
- Issue *titles* stay owned by each producer; only the body is contracted here.
- The PR-body gate (`check-pr-hygiene`) is not modified: this change states the mapping and reuses it.
