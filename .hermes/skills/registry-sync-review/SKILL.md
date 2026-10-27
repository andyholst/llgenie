---
name: registry-sync-review
description: Use when an llgenie registry-sync PR is green and the store's trend list must be reviewed — name the VRAM→model→highest-t/s engine answer and write ONE issue body to registry-review.md.
version: 1.0.0
author: Asimov Agent
license: CC-BY-4.0
metadata:
  hermes:
    tags: [llgenie, bots, registry-sync, review, trend-list]
---

# Registry-sync review

The weekly `registry-sync` job vendors a new `data/models.json` and opens a PR. This leg exists for
the moment that PR is **green**: the store can land, so someone must say whether llgenie still
answers the user's question — *at the VRAM this machine has, which trending model do I get, and which
inference server gives the most t/s for it?* — and file the change that follows.

It is a review, not an implementation: the only thing it writes is the issue body.

## Inputs

- `registry-review-in.md` at the repo root, rendered by `make registry-review-brief` from the store
  and the vendored engine params (no Hub, no network). It carries:
  - the **precondition**: the open `chore/registry-sync` PR, its URL, and every check's bucket;
  - the **store**: `generated_utc`, model and engine counts, and whether the committed trend-list
    matrix describes this store or an older one;
  - the **VRAM selection check**: per architecture and card size, the models `trend_list()` lists
    and, for each, the server `rank_engines()` puts first with its measured t/s;
  - every **finding**: `slower-than-class` (the named server is not the fastest of its own rank
    class), `no-engine` (a listed model no image can run), `unmeasured` (a named server with no
    measured t/s), `empty-tier` (a card that lists nothing).
- `data/models.json`, `data/model_contract.json`, `tests/fixtures/trend-list-matrix.json`,
  `data/engine-skill-gap.json` and `AGENTS.md` — read them when a fact needs checking; the brief is
  an index, the store is the data.

## Output

`registry-review.md` at the repo root, and nothing else:

```
VERDICT: review
TITLE: sync review: <the one thing that must change, with the store's generated_utc>
# Issue body, in this repository's issue shape

Issue:
<the measured symptom — the card, the model, the server the list names and the t/s that beats it>

## What the green store answers

<the VRAM → model → server (t/s) answer, per card size llgenie sells, quoting the brief's numbers>

## What this implies for llgenie

<ordered, checkable work items; each names the file/command it touches and what "done" is>

## Not covered

<what belongs to its own issue, with the issue number when one exists>

- **Test:** <the test or make target that will prove each claim where one exists>
```

```
VERDICT: clear
REASON: <one line: the list and the servers are right for this store, and nothing must change>
```

## Rules

- **`review` only when the green precondition holds.** If the brief says `action=skip`, the sync PR is
  missing, red or pending — answer `clear` with that as the REASON. Never review a store that cannot
  land.
- **Quote measured numbers, never an adjective.** "At 16 GB on cuda the list names llama.cpp at 108.3
  t/s, but Strata measured 140.0 t/s on the same card class" is a finding; "the ranking looks off"
  is not.
- **The rule is the repository's, not yours.** `rank_engines()` prefers a figure proven on this card
  class over a raw maximum (issue #225), so a datacenter figure or a bigger card's figure is not a
  defect. A `slower-than-class` finding is only real when the faster engine has the SAME rank class.
- **One issue, one objective.** The change report (`make sync-change-issue`, #704) already states what
  the diff changed; this issue states what the *green* store implies for the pick, the trend list and
  its goldens. Name the change report's number in `Not covered` instead of repeating it.
- **Deferred work is a linked issue, not prose.** An item you are not asking this issue to fix goes
  in `Not covered` with its own issue number.
- **Never edit the store, the matrix, the goldens, a skill, or a branch** — no `make`, no `git`, no
  `gh`, no PR, no issue comment. The deterministic publish step files the issue from your body.
