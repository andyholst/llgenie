# 2026-10-23 — the run-failure reactor files only work that is still work (#565)

Issue: **#565** (implemented here). Related, filed from the same audit and **not** implemented in this
change: **#563** (the duplicate sweep cannot see reactor-filed issues) and **#564**
(`issue-dedup-pick DRY=1` writes `dedup-in.md`). Also existed already: #349 (the reactor's hand-maintained
`workflows:` roster). PR: this branch's PR against `asimov-agent/llgenie:main`.

## What was measured

Auditing the scheduled fleet against its own decision lines found the reactor's Route B filing one issue
per failed run, and **all six** open `agent:implement` issues were failures that had already been
superseded:

| issue | event | the run's PR | state |
|---|---|---|---|
| #557 | pull_request | #554 | merged 10:09Z |
| #551 | pull_request | #539 | merged 09:12Z |
| #542 | pull_request | #539 | merged 09:12Z |
| #537 | pull_request | #533 | merged 05:26Z |
| #507 | pull_request | #506 | merged 2026-10-22 09:44Z |
| #548 | push (main) | — | next CI run on main green at 10:19Z |

With `scripts/issue_implementer.py`'s `MAX_PER_DAY = 3` and oldest-first picking, that queue is two full
days of the implementer's budget spent on defects that were green before the issues existed.

## The decision

Route B now asks one question — *is the subject of the failure still there?* — and only on its own path,
after Route A has already found no pushable PR:

- `pull_request` event → file only when an **open** PR exists for the head (`open_pr_exists`, an
  unfiltered `head:<branch>` search). `resolve_run_pr.open_pr_for_head` narrows by owner and would make a
  stranger's live PR look absent, so the superseded check deliberately does not reuse it.
- `push` event → file only when no **later run of the same workflow on the same branch concluded
  `success`** (`gh run list --branch … --workflow …`, ordered by `createdAt`).
- **an unreadable answer is UNKNOWN.** A failed `pr list`/`run list` read prints that it could not be read
  and the failure is filed. A failed read must never delete a real work item.
- a **fifth-party fork** head is UNKNOWN too: no token this repository holds can read it, so it is never
  called superseded.

The sha-scoped marker is unchanged on purpose: `macos / unit` failed on the engine-image digest, the
README dispatch table and a cron collision within six hours, so collapsing by workflow/job would merge
distinct defects. Cross-issue grouping is #563's job.

## Verification

- `tests/test_run_failure_reactor.py` — 17 pass in the CI test image. Four new scenarios: a merged-PR run
  files nothing, a superseded main push files nothing, a later **failure** does not supersede an earlier
  one, and an unreadable run list is not a supersede.
- Proven against the base, not just claimed: with `origin/main`'s `run_failure_reactor.py` swapped in, the
  three fix-bearing tests FAIL (`test_a_merged_pr_run_files_nothing`,
  `test_a_superseded_main_push_files_nothing`, `test_an_unreadable_run_list_is_not_a_supersede`) and the
  guard test passes on both — exactly the asymmetry a real fix has.
- `make openspec-validate NAME=reactor-superseded`, `make lint`, `make check-docs`, `make test-unit`.

## Status

The six measured duplicate issues are closed with their merged-PR / green-main evidence. The bot still
never merges; CI's `auto-merge` owns landing.
