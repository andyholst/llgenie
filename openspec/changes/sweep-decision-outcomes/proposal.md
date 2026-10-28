# The sweep's decision has four outcomes, never three (issue #801)

## Why

`rebase-bot` reported `success` while leaving PR #789 conflicted (run 40695154969), and crashed on the next
dispatch instead of deciding (run 40700214889, *"refusing to treat a crashed decision as 'nothing to do'"*).
Both are the same missing distinction: the sweep had no single place that named what a read of one PR
produced, so "uncomputed" and "could not read" could each decay into "nothing to do".

## What changes

- `rebase_bot_sweep.outcome(state, crashed=False)` classifies one PR into exactly one of
  `REBASE` / `NONE` / `DEFER` / `ERROR`, and the sweep uses it as the only place the rule lives.
- `UNKNOWN` is `DEFER` (its own outcome, re-queried then deferred by name — #453) and a crashed read is
  `ERROR` even when the state it did read looks rebasable (#801).
- Tests assert each outcome **and** the outcome it must not be, plus one structural control that the four
  values stay distinct, so a refactor cannot collapse them again.

## What does not change

The actor, the claim protocol, the daily cap and the lease push. This is the decision only.
