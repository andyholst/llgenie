# A GREEN registry-sync PR is reviewed into ONE agent:implement issue

## Why

Two bots now bracket the weekly store: `registry-sync` vendors it and opens a PR when its gates pass,
and `sync-change-issue` (#704/#705) files what the store *changed*, even when a gate is red. Neither
answers the question the green PR exists for:

> At the VRAM this machine has, does the trending list still list models, and does each row name the
> inference server with the highest t/s that fits that card?

That answer is read by eye today, per run, from a 20k-line JSON diff and an 81-case matrix fixture —
and the store is frozen: `data/models.json` still carries `generated_utc 2026-10-13T14:31:40Z` on
`main@2cbfb11`, because no sync PR has landed since (#534, #659, #684). Run against that store, the
check in this change already reports **92 `no-engine` findings over the 80 cases**, on three models —
`nemotron-3.5-lightning-30b-a3b` (60 cases), `glm-5.3-flash` (16) and `llama-3.1-8b` (16) — each listed
on an architecture where no engine image can run it, which is the class #686 is about. #669 (the order is
global, not tier-local), #677/#693 (the suite pins old rows) and #687 are facets of the same missing
review.

## What changes

- **`scripts/registry_review.py`** — stdlib + `model_engine_pick`, no network:
  - `brief` decides the **precondition** (an OPEN `chore/registry-sync` PR whose every check bucket is
    `pass`; a missing PR, a `fail`, a `pending` or a `cancel` is `action=skip`) and renders the **VRAM
    selection check**: for every `(arch, vram, ram)` the matrix is built from, the models
    `trend_list()` lists for that card and, per model, the server `rank_engines()` puts first with its
    t/s. Findings: `slower-than-class` (the named server is not the fastest of its own rank class),
    `no-engine`, `unmeasured`, `empty-tier`.
  - `publish` files ONE issue labelled `agent:implement` from the leg's body, keyed by a
    `<!-- registry-sync-review: <generated_utc> -->` marker: a re-run edits it, never duplicates it,
    and the store's change issue (#704) is linked rather than restated.
- **`.hermes/skills/registry-sync-review/SKILL.md`** — the one agent leg's contract: Inputs (the
  brief), Output (`registry-review.md`: `VERDICT`/`TITLE` + a body in the repository's issue shape),
  Rules (quote measured numbers; `rank_engines`' proven-class rule, #225, is not a raw max; never edit
  the store, the matrix, a golden or a branch).
- **`Makefile`** — `registry-review-brief`, `registry-sync-review` (the leg, inside the agent image,
  redacted transcript), `registry-review-publish`; all `.PHONY`, all documented.
- **`.github/workflows/registry-sync-review.yml`** — hourly `:23` + `workflow_dispatch`, the owner/
  collaborator guard, and every secret-spending step behind `steps.brief.outputs.action == 'review'`,
  so a run with no green PR costs nothing.
- **`tests/test_registry_review.py`** — the real `selection()` over a real store built in a temp dir
  (plus an order that is wrong, to prove the detector fires), the real `brief()`/`publish()` with `gh`
  as the only stand-in, and the workflow's gating and skill contract read as text.

## Impact

`registry-sync` keeps ownership of the store and of `sync-change-issue`; this bot adds the review of a
store that can LAND and the work item that follows. It never merges, never pushes, never edits the
store, the matrix fixture or a golden — the issue it files is what the implementer works.

Not in this change: the ranking rule itself (#669); re-deriving the old-row goldens (#677/#693); and
rewriting `tests/fixtures/trend-list-matrix.json` (the brief REPORTS its staleness).
