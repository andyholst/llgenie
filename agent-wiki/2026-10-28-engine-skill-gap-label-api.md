# 2026-10-28 — the spawned engine-skill issue is queued through the REST label API

Issue [#724](https://github.com/asimov-agent/llgenie/issues/724), PR
[#826](https://github.com/asimov-agent/llgenie/pull/826). OpenSpec change
`fix-engine-skill-gap-label-api`.

## What was verified

- **The failure is real and measured, three runs in a row.** registry-sync `40682255828`
  (2026-10-28T11:44Z), `40554900569` (2026-10-27T17:54Z), `40472116087` (2026-10-27T08:14Z) — all
  three die in `make spawn-engine-skill-issues` with
  `GraphQL: Resource not accessible by personal access token (addLabelsToLabelable)` on
  `gh issue edit 774 --add-label agent:implement`. The issue was filed, the queue label was not, and
  `scripts/issue_implementer.py` selects on that label — so the work item routed to nobody.
- **Two write paths, both untrustworthy.** `gh issue edit --add-label` is GraphQL and refused
  outright by the PAT; `gh issue create --label` is silently dropped on the runner path (the same
  defect #785/#786 measured on the security filer, whose issues #781–#784 arrived with zero labels).
  The old read-back (`gh issue view --json labels`) used the other transport, so it could agree with
  a write that never happened.
- **The new rules catch the old tree.** With `scripts/engine_skill_gap.py` stashed (old code) and the
  new assertions in place: `4 failed, 74 passed`. With the change: `78 passed` — in
  `llgenie/test:latest`, run as
  `docker run --rm -u root -v "$PWD":/repo -w /repo llgenie/test:latest python -m pytest
  tests/test_engine_skill_gap.py -q`.

## Decisions

- **The POST is the write, the read-back is the verdict.** `set_labels()` labels through
  `POST repos/<repo>/issues/<n>/labels` (one `-f labels[]=<name>` per label) and then reads
  `GET repos/<repo>/issues/<n>/labels --jq .[].name`; a missing label is `SystemExit` naming the
  issue, never a warning. This is PR #786's shape for the security filer, applied to this leg so the
  two can be consolidated later without a rewrite.
- **`--label` is gone from the create.** It stays only in `scope`-free prose; passing it would keep a
  write nobody can trust in the code for the next reader to rely on. `bug` and `agent:implement` are
  applied by the same POST, in one call.
- **An open, unlabelled tracking issue is repaired, not duplicated.** `ensure_queue_label()` restores
  `agent:implement` on the existing issue, so a sync that failed before this fix is fixed by the next
  run instead of needing a human to label #774 by hand.
- **The docs that described the broken mechanism were corrected in the same commit** —
  `docs/BOTS.md` claimed `gh issue edit --add-label` was the working write and
  `docs/ARCHITECTURE.md` said the same in prose; both now state the REST POST + read-back and the
  measured refusal, so the documentation cannot drift back.
- **Scope held.** The four `test-unit` failures visible in the same sync run belong to #775 (they
  assume a vendored registry that never grows an unresolved engine) and the other producers that
  still use `--label`/`--add-label` are #819 (one shared helper + `make check-issue-labels`);
  neither is folded in here.
- **Both `registry-sync` legs are fixed in this one change.** The issue body names
  `registry_change_issue.py` (the change issue, #710/#749) while the run's failure names the spawned
  tracking issue `#774` — same defect class, same workflow, one helper shape, so both
  `scripts/registry_change_issue.py` and `scripts/engine_skill_gap.py` now POST + read back.
- **Live proof on the real tracker.** Issue #773, filed unlabelled by the 2026-10-27 sync, went from
  `[]` to `['agent:implement']` through `set_labels()` and the read-back printed it; `gh api … --jq
  '.labels|length'` → `1` independently. The queue that had no entry now has one.

## Status

Open PR on `fix/engine-skill-gap-label-api`; the gate list is `make test-unit`, `make lint`,
`make check-docs`, `make check-wiring`, `make openspec-validate NAME=fix-engine-skill-gap-label-api`.
Merge is CI's (`auto-merge`), never a hand merge.

## Related

- `agent-wiki/2026-10-27-engine-skill-automation.md` — the spawn leg this repairs (#757).
- #785 / PR #786 — the same REST label + read-back fix for the security filer.
- #229 — the unskilled-engine gap the tracking issue serves.
