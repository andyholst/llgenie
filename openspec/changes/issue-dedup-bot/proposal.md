# A duplicate sweep, four times a day

## Why

The refiner improves ONE issue per run and the implementer implements ONE; neither ever compares two open
issues, and no workflow runs any dedupe at all (the cron roster has no such job, and `scripts/issue_cleaner.py`
closes an issue a *merged PR already implemented*, #325 — a different problem). Duplicates are caught only when
an implementer `close` verdict happens to read both: #400 was closed as a duplicate of the unlabelled #254, and
#440 of the unlabelled #399, and twice the defect stayed unimplemented until #521 taught the close path to queue
the canonical issue.

Measured on `main` (`333344c`): 15 open `agent:implement`, 1 `agent:ready`, 3 `agent:refined` — nothing compares
any two of them.

## What Changes

- **`scripts/issue_dedup.py`** — the cross-issue decision: candidates are the open, **unclaimed** issues
  (any agent label excludes an issue: `agent:implement`, `agent:ready`, `agent:refined`, `agent:closed`,
  `agent:duplicate`), and a **bot-generated tracker issue** — its body carries a `<!-- <name>-bot:` marker —
  is excluded as well, since two generated refresh issues are near-identical by construction (measured
  #494/#517 at 0.78, which the first live run produced before this rule); the pair is the highest title+body token Jaccard at/above 0.30, older as canonical; the
  agent answers `DUPLICATE: #<older>` + `EVIDENCE` or `DISTINCT:` + `REASON`; and the apply path retires the
  **copy** only — a comment citing the canonical, the `agent:duplicate` label, the close, then the canonical
  queued with `agent:implement` when unqueued. A duplicate with no `EVIDENCE` is refused, and the apply path
  re-checks the copy for agent labels before touching it.
- **`make issue-dedup-pick` / `issue-dedup` / `issue-dedup-apply`** — the three steps, one entry point each.
- **`.github/workflows/issue-dedupe.yml`** — `cron: "37 */6 * * *"` (four times a day, its own minute) plus
  `workflow_dispatch` behind the byte-identical owner/collaborator `guard` job; one pair per run; the agent leg
  inside the agent image with its transcript redacted (`scrubbed_run`).

## Impact

- The same defect filed twice is retired once, with the canonical issue queued so the work is implemented.
- The sweep cannot race the bots that do the work, and a duplicate close cannot lose the canonical issue.
