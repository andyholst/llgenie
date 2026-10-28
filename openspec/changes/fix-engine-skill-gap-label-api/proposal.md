# fix-engine-skill-gap-label-api — proposal

Issue: [#724](https://github.com/asimov-agent/llgenie/issues/724) — PR
[#826](https://github.com/asimov-agent/llgenie/pull/826)

## Why

`registry-sync` files one tracking issue per NEW unskilled registry engine so the bots can scaffold
the skill (#757). On the runner's PAT that issue is filed and then never queued, and the step is red:

```
[engine-skill-gap] gh issue edit 774 --repo asimov-agent/llgenie --add-label agent:implement
  failed (1): failed to update https://github.com/asimov-agent/llgenie/issues/774:
  GraphQL: Resource not accessible by personal access token (addLabelsToLabelable)
make: *** [Makefile:317: spawn-engine-skill-issues] Error 1
```

Measured on three consecutive registry-sync runs — `40682255828` (2026-10-28T11:44Z),
`40554900569` (2026-10-27T17:54Z), `40472116087` (2026-10-27T08:14Z). The issue carries neither
`agent:implement` nor `bug`; `scripts/issue_implementer.py` selects on exactly that label, so the
work item exists and routes to nobody.

Two GitHub write paths are involved and neither can be trusted:

- **`gh issue edit --add-label`** is GraphQL (`addLabelsToLabelable`) and is refused outright by the
  PAT — the error above.
- **`gh issue create --label`** is silently DROPPED on the runner path: the issue is created, the
  command exits 0, and the label is absent (the same defect #785/#786 measured on the security
  filer, issues #781–#784 filed with zero labels).

Read-back was only ever done through `gh issue view --json labels`, which can agree with a write that
never happened, and the create path passed `--label bug` and trusted it.

## What Changes

- **`scripts/engine_skill_gap.py`**
  - `_gh_api` — `gh api` takes no `--repo`; the path carries the repository.
  - `_issue_labels` — reads the labels over the SAME REST endpoint the write uses
    (`repos/<repo>/issues/<n>/labels --jq .[].name`), not `gh issue view`.
  - `set_labels` — `POST repos/<repo>/issues/<n>/labels` with one `-f labels[]=<name>` per label,
    then a read-back that **fails the step** (SystemExit, naming the issue and the missing label)
    when a label did not stick.
  - `ensure_queue_label` — an existing tracking issue that lost `agent:implement` is repaired
    through the API on the next sync instead of staying unroutable.
  - `open_issue` — `gh issue create` passes **no** `--label`; `bug` and `agent:implement` are
    applied by `set_labels` (one POST + one read-back) as soon as the create returns a number.
- **`tests/test_engine_skill_gap.py`** — the `gh` stand-in answers the REST label endpoints only
  (its `issue create` stores no label, the measured CI behaviour) and records every argv, so the
  tests assert the request the product builds: exactly one `api -X POST …/labels` per created or
  repaired issue, a `--jq .[].name` read-back, no `issue edit`/`issue view` GraphQL write, and a
  loud failure when the read-back is missing the queue label.
- **`agent-wiki/2026-10-28-engine-skill-gap-label-api.md`**, **`CHANGES.md`** — the dated record and
  its index row.

## Not covered

- **The four `test-unit` failures in `tests/test_engine_skill_gap.py` seen in the same run are
  #775's tracker**, not this change: they assume the vendored registry never grows an unresolved
  engine, so they fail when the sync job's freshly synced `data/models.json` is the one under test.
  This branch does not touch the vendored registry and the suite is green on it (78 passed).
- **The other producers that still label the untrustworthy way** — `registry_review.py`,
  `run_failure_reactor.py`, `issue_dedup.py`, `issue_implementer.py`, `issue_refiner.py`
  (`--label` on create and/or `--add-label`) — are filed as [#819](https://github.com/asimov-agent/llgenie/issues/819)
  (one shared helper + a `make check-issue-labels` guard), because each has its own queue and its
  own tests; folding them in here would make one unreviewable change.

Refs: #757 (the spawn leg), #785/#786 (the same REST label+read-back fix for the security filer),
#229 (the unskilled-engine gap this issue serves).
