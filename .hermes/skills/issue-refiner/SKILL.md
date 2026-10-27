---
name: issue-refiner
description: Use when an llgenie refiner run must review ONE open issue and write its verdict to refine.md — restate it, or say it is already clear.
version: 1.0.0
author: Asimov Agent
license: CC-BY-4.0
metadata:
  hermes:
    tags: [llgenie, bots, issue-refiner, review]
---

# Issue refiner

The refiner spends the implementer's spare capacity on the *review* of a not-yet-implemented issue.
It is a review, never an implementation: the only thing it writes is its verdict.

## Inputs

- `refine-in.md` at the repo root: an issue, its **whole comment thread** (oldest first), and the
  review instruction with the exact verdict shapes.
- `fetched/index.md`: the text of every URL the issue or its thread names, pre-fetched by the host
  before you started. This is what the outside world actually says — use it instead of guessing. A
  URL it lists as COULD NOT BE FETCHED is UNKNOWN, not false.
- `AGENTS.md` for the repository's rules.

## Output

`refine.md` at the repo root:

```
REFINE: refined
RESTATED:
## Problem
<what is wrong, observed — the measured symptom, not the ticket title>
## Why it matters
<the consequence of leaving it: what breaks, what it costs, what it blocks>
## How we fix it
<numbered, plain language — what changes, and why that addresses the cause>
## Benefit
<what the reader gets once it is fixed; what stops happening>
## Acceptance criteria
- [ ] <one provable outcome per line, tickable by a reviewer>
## Technical
<LAST: files, make targets, tests, gates, measured numbers>
REASON: <one line: what was missing>
```

```
REFINE: already-clear
REASON: <one line: why nothing needs adding>
```

## Rules

- **`refined` requires `RESTATED:` in the repository's shape** — `## Problem`, `## Why it matters`,
  `## How we fix it`, `## Benefit`, `## Acceptance criteria` (one `- [ ]` item each), then
  `## Technical` last. A restatement the reviewer cannot act on is worse than no comment; a
  restatement missing a section is not a restatement (`make check-issue-bodies` holds the
  producers to the same shape).
- **`already-clear` is a real answer**, not a way out — say what makes the issue actionable already.
- **A decision the thread leaves open is a question in the restatement, not a decision you make.**
  Name the options and what each implies; the owner picks.
- **Change nothing else.** No code, no branch, no PR, no comment on the issue, no edit outside
  `refine.md`. The host posts the comment and applies the `agent:refined` label.
