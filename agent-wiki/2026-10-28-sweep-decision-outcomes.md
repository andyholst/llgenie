# The sweep's decision has four outcomes, never three (#801)

`rebase-bot` failed twice in one evening in two opposite directions. Scheduled run **40695154969** reported
`success` while leaving PR #789 conflicted — a green run behind a PR that had never been touched. Hand
dispatch **40700214889** then crashed, and its own workflow refused to hide it: *"the rebase sweep failed
(make rebase-bot-sweep rc=N); refusing to treat a crashed decision as 'nothing to do'"*.

Both are one missing distinction. The sweep had no single function that said what a read of one PR
produced, so two different facts — GitHub has not computed the merge state yet, and the read raised — could
each decay into "nothing to do" at different call sites. `outcome(state, crashed=False)` is that function:

```
DIRTY, BEHIND          -> REBASE
MERGEABLE, BLOCKED, CLEAN -> NONE
UNKNOWN                -> DEFER     (its own outcome, re-queried then deferred by name, #453)
crashed                -> ERROR     (even when the state it did read looks rebasable, #801)
```

`crashed` is an argument rather than a separate code path on purpose: a failed read is an outcome of the
same decision, so a caller that only remembers three outcomes cannot drop it. The tests assert each outcome
**and the outcome it must not be** — `UNKNOWN is not NONE`, a crashed `DIRTY` is not `REBASE` — because
those are the assertions a refactor breaks first, plus one structural control that the four values stay
distinct.
