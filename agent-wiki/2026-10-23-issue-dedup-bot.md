# 2026-10-23 — the duplicate sweep, four times a day (#553)

**Issue:** [#553](https://github.com/asimov-agent/llgenie/issues/553) · **PR:** the PR that closes it

## What was missing

No workflow compared two open issues, and the cron roster had no dedupe job at all. The refiner improves ONE
issue per run, the implementer implements ONE, so the same defect filed twice was implemented twice — or the
better specification was retired: #400 was closed as a duplicate of the unlabelled #254, #440 of the unlabelled
#399, and both times the defect stayed unimplemented until #521 taught the close path to queue the canonical.
`scripts/issue_cleaner.py` is a different bot (it closes an issue a merged PR already implemented, #325) and no
workflow ran it either.

## What landed

- `scripts/issue_dedup.py`: **candidates are the open, unclaimed issues** — any agent label (`agent:implement`,
  `agent:ready`, `agent:refined`, `agent:closed`, `agent:duplicate`) excludes an issue as both candidate and
  target, so the sweep cannot race the implementer/refiner. The pair is the highest title+body token Jaccard at
  or above 0.30, the older issue canonical; the agent answers `DUPLICATE: #<older>` + `EVIDENCE` or `DISTINCT:`
  + `REASON`; the apply path posts one comment citing the canonical, adds `agent:duplicate`, closes the copy,
  and queues the canonical with `agent:implement` when unqueued. No evidence, no close.
- `make issue-dedup-pick` / `issue-dedup` / `issue-dedup-apply` — the three steps the workflow calls.
- `issue-dedupe.yml`: `cron: "51 */6 * * *"` (**four times a day**, its own minute) + `workflow_dispatch` behind
  the byte-identical owner/collaborator guard; one pair per run; the agent leg runs inside the agent image and
  its transcript is redacted (`scrubbed_run`). A crashed pick and an empty `dedup.md` both fail loudly instead
  of reporting a green no-op.

## Verified

- `pytest tests/test_issue_dedup.py` in `llgenie/test:latest` → **12 passed** (every protected label, candidate
  filtering, pair choice with the older canonical, the file the agent reads, close+queue, the no-evidence
  refusal, a claimed copy left untouched, a distinct verdict changing nothing).
- `tests/test_workflow_guards.py` + `tests/test_dispatch_forms.py` + `tests/test_wiring.py` green after the
  README dispatch table was regenerated.
- `make lint`, `make check-workflows`, `make check-docs`, `make openspec-validate NAME=issue-dedup-bot`,
  `make openspec-tasks-check` green; `make test-unit` runs in the PR's checks.

## Related

- #522 (a refine parked an issue forever) landed first, so a marker label can no longer remove an issue from
  the implementer's queue — the sweep's own label (`agent:duplicate`) is on a closed copy and safe either way.
- #521 (a close queues the canonical issue) is the rule this bot reuses.
