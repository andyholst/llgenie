# A green registry-sync PR is reviewed into ONE agent:implement issue

Issue #709 (this change), PR #720. Complements #704/#705 (`sync-change-issue`, which states what a store
*changed*, even when a gate is red) and answers the question the green PR exists for: at each VRAM
llgenie sells, does the trending list list models, and does each row name the inference server with the
highest t/s that fits that card?

## What was verified against the spec

- **The precondition** (`openspec/changes/registry-sync-review/specs/registry-sync/spec.md`, "only runs
  for a GREEN registry-sync PR"): `sync_pr()` reads the open `chore/registry-sync` PR and every check
  bucket; a `pending` check is not green and is named in the reason; no open PR is a `skip` with the
  reason. Pinned by `tests/test_registry_review.py::test_the_precondition_is_every_check_green_on_an_open_sync_pr`
  and `::test_no_open_sync_pr_is_a_skip_with_a_reason`.
- **The selection check** runs the product's own `trend_list()` / `rank_engines()` over the vendored store
  and the committed engine params — no Hub, no model. `selection(ranker=…)` exists so a test can hand the
  checker an ORDER THAT IS WRONG; that is the only way to prove the detector fires, because a correct
  `rank_engines()` never returns a slower same-class engine first. Pinned by
  `::test_a_list_that_names_a_slower_server_of_the_same_class_is_a_finding` (and the correct-list,
  `no-engine` and `empty-tier` cases beside it).
- **One issue per store**: publish creates exactly one issue labelled `agent:implement` and edits it on a
  re-run; a `VERDICT: clear` files nothing; the store's change issue is linked, not restated. Pinned by
  four tests in the same file.
- **Measured on the real tree** (`main@2cbfb11`): `make registry-review-brief` prints
  `action=skip` / `reason=no open `chore/registry-sync` PR` and still renders 92 `no-engine` findings over
  the 80 cases, on three models — `nemotron-3.5-lightning-30b-a3b` (60 cases), `glm-5.3-flash` (16) and
  `llama-3.1-8b` (16) — each listed on an architecture no engine image can run it on. The store itself is
  frozen at `generated_utc 2026-10-13T14:31:40Z` (#534/#659/#684),
  which is why the weekly sync PR never turns green today: this bot reports that state, it does not fix it.

## Decisions taken

- **A separate issue from #704's change report.** One objective per issue: the change report indexes the
  diff; this one states what the *green* store answers and what must follow. The link runs one way (ours
  names theirs) so the two cannot drift into paraphrases of each other.
- **No model in the precondition or the table.** Both are facts a script derives; the leg's only job is
  the judgement (which finding matters, what to change) and its only output is the issue body.
- **Hourly, not `workflow_run`.** A sync PR becomes green only after CI runs on it, so a `workflow_run`
  trigger on `registry-sync` would fire before the checks exist. The brief's `action=skip` makes an hourly
  poll free when nothing is green.
- **The brief REPORTS a stale matrix fixture, it does not rewrite it** (that is #677/#693's change), and
  the ranking rule itself stays #669's.

## Status

Implemented and verified: `make test-unit` (selection + brief + publish + workflow/skill contract),
`make check-agent-skills`, `make check-docs`, `make check-wiring`, `make check-dispatch-forms`,
`make check-workflows`, `make openspec-validate NAME=registry-sync-review`.
