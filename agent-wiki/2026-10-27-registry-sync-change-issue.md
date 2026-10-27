# 2026-10-27 — a changed store opens ONE issue that states what changed

Implements issue #704 (OpenSpec change `registry-sync-change-issue`).

## What was wrong (measured)

The weekly `registry-sync` regenerates `data/models.json`, the README, the vendored contract and four
derived tables, then stops: the PR step is `skipped` whenever a gate is red (`40450580364` — `test-unit`
130 failed / 14707 passed, steps 10 and 11 skipped). Nobody was told what changed in the store; learning
that 89 models and 18 engines had appeared meant diffing a 20k-line JSON by hand.

That is the input #677/#693 are missing: both say "re-derive against the new store", and neither can start
without the change list.

## What was decided

A deterministic step, `scripts/registry_change_issue.py`, with two commands:

- `report` compares `HEAD:data/{models.json,model_contract.json,trending-README.md,trending-quant-catalog.json,mode…}`
  plus the matrix and skill-gap fixtures with the working tree's, and renders the facts: `generated_utc`
  old → new, model/engine counts, added/removed/renamed model ids (capped at 40 with a pointer at the
  diff), new and gone engines, the `formats` vocabulary seen, every contract change (required keys added
  or removed per model row, new `backend` enum values), README row count and added/removed rows, and the
  derived-table counts.
- `open` files **one** issue titled `sync: review the <generated_utc> trending registry`, labelled
  `agent:implement`, whose body is the report in this repository's issue shape plus a "what this implies"
  checklist (re-derive the goldens #693/#677; decide each new engine #673/#686; teach the contract reader
  #694; check the formats vocabulary #687/#692; run the job's own gates). A hidden marker
  `<!-- registry-sync-changes: <utc> -->` makes a re-run UPDATE that issue instead of filing a second.

The workflow runs it with `if: always() && steps.diff.outputs.changed` — on purpose: the analysis matters
most when a gate is red, because that is exactly when the store cannot land and the next change is written
from it.

No model in the path. A summariser over a 20k-line diff cannot be re-run to the same answer; the diff is
the artefact and this is its index. The judgement stays with the agent that picks the issue up.

## Verified

- Unit tests (4) over the real `compare()`/`render()` with two stores built in a temp dir: the report names
  an added model, a new engine, an added contract key and a new `backend` enum value, and says what to do;
  a second `open` for the same marker edits the existing issue (`issue edit 704`), a fresh one creates
  exactly one issue with `--label agent:implement`, and `--dry` mutates nothing. `gh` is the only stand-in.
- Real data: `make sync-registry` (23 → 112 models, `generated_utc` 2026-10-26T22:32:58Z) then
  `make registry-change-report` renders the body — 89 added models, 24 → 42 engines, the two changed files.
- `make test-unit`, `make check-wiring`, `make check-dispatch-forms`, `make check-docs`, `make lint` and
  `make openspec-validate NAME=registry-sync-change-issue` recorded in `tasks.md`.

## Status

Implementation complete on `feat/sync-change-issue`. Not in this change: the ranking rule the trend list
is built on (#669), which is why the sync still does not land, and archiving each sync as a timestamped
snapshot (the comparison is against `HEAD`, which is the previous store).
