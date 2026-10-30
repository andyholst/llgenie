# 2026-10-30 — issue #1061: `ci_scope.select()` refuses a class name it does not know

## What was wrong

`scripts/ci_scope.py` decided in #860 that an unreadable diff fails **open** in the library, not in
`main()`, so every caller inherited the safe answer; and it refuses to hide a class nobody claimed.
The sibling public API `select()` never got that guard. It builds `wanted = set(classes)` and keeps a
job only when one of its `needs` intersects that set, so a name that is not a key of `CLASSES`
matches nothing and every job needing it is dropped with no exception, no stderr and a zero exit.

Measured at `main@9da3ee2e` (`def select()` at line 180, `grep -c "CLASSES\|raise\|assert"` on its
body → 0):

```
>>> len(c.JOBS)
10
>>> sum(r[1] for r in c.select(list(c.CLASSES)))   # every real class
10                                                 # 10/10 — correct
>>> sum(r[1] for r in c.select(['tests_typo']))     # one mistyped name
2                                                  #  2/10 — 8 jobs vanish, no error
```

That is the quiet empty set #824 exists to forbid, one layer down. The CLI avoids it only because
`main()` passes `classify()`'s output, always drawn from `CLASSES` — a guard at the visible call site
rather than in the API that is reused.

## What the change is

- `select()` computes `unknown = sorted(set(classes) - set(CLASSES))` and raises `ValueError` naming
  the unknown entries and the valid set:
  `unknown class tests_typo — valid classes are docs, skills, workflows, scripts, tests, data,
  containers, engines, security`.
- Nothing else moves: `classify()`, `JOBS`, the selection logic and every caller (`main()` at
  `select(classes)`) are untouched, and an **empty** list stays legal — the documented `--paths ''`
  always-jobs case.
- `tests/test_ci_scope.py` gains four cases: the raise names the bad name and every valid class, every
  unknown entry is named (not just the first), `select([])` returns exactly the always-on jobs, and
  `select(list(CLASSES))` returns 10 of 10.

## Negative control

The two raise cases were committed *before* the guard and run against the old `select()`:
`2 failed, 41 passed` — both failures `Failed: DID NOT RAISE <class 'ValueError'>`. With the guard in
place the same file reports `43 passed`. So it is the raise that changed, not the job selection: the
`select([])` and `select(list(CLASSES))` cases passed on both trees.

## Decisions

- **The guard lives in `select()`, not in `main()`.** #860's lesson, applied to the sibling API: the
  library is the reusable surface, so the loud refusal belongs where every importer inherits it.
- **An empty list is not an error.** `[]` is the documented `--paths ''` case (nothing read → the
  always-on jobs); making it raise would change a legal selection. Only a name that is not a class is
  a caller bug.
- **No message text is trimmed to a count.** The message names every unknown entry *and* every valid
  class, so a typo is fixed from the log alone, without opening `ci_scope.py`.

Issue: #1061
