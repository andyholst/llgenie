---
name: ci-scope-select-guard
about: ci_scope.select() refuses an unknown class name instead of silently dropping its jobs
status: active
---

# select() refuses a class name it does not know (issue #1061)

## Proposal

`scripts/ci_scope.py` decided in #860 that an unreadable diff must fail OPEN in the library itself,
so every caller — not just the CLI — got the safe answer, and it refuses to hide a class nobody
claimed. The sibling public API `select()` never got the same treatment: it builds `wanted =
set(classes)` and keeps a job only when one of its `needs` intersects that set, so a class name that
is not a key of `CLASSES` matches nothing and every job needing it is dropped in silence. That is the
same quiet empty set, one layer down: a mistyped name produces a green-looking 2-of-10 run with no
exception, no stderr and a zero exit.

## Motivation

Measured at `main@9da3ee2e` (`scripts/ci_scope.py`, `def select()` at line 180, no guard):

```
>>> len(c.JOBS)
10
>>> sum(r[1] for r in c.select(list(c.CLASSES)))   # every real class
10
>>> sum(r[1] for r in c.select(['tests_typo']))     # one mistyped name
2                                                   #  8 jobs vanish, no error
```

`select()` is the module's stated library surface (a test, a script, a future workflow importing it),
and `main()` only avoids the bug because it happens to pass `classify()`'s output. A guard at the
call site that is visible, rather than in the API that is reused, is how the defect survives.

## Change

- `scripts/ci_scope.py`: `select()` computes `unknown = sorted(set(classes) - set(CLASSES))` and
  raises `ValueError` naming the unknown entries AND the valid class set. Nothing else changes:
  `classify()`, the job table, the selection logic and every caller are untouched, and an EMPTY list
  stays legal (the documented `--paths ''` always-on case).
- `tests/test_ci_scope.py`: four cases — the raise names the bad name and every valid class, several
  unknown entries are all named, `select([])` still returns exactly the always-on jobs, and
  `select(list(CLASSES))` still returns 10 of 10. The first two are the negative control: they fail
  with `DID NOT RAISE` against the old `select()` and pass after the fix, so it is the *raise* that
  changed, not the job selection.
- `agent-wiki/` note + `docs/changes.d/` fragment (the index row lives in the fragment).

## Acceptance

- [x] `select(["tests_typo"])` raises `ValueError` whose message contains the bad name and the valid
      class set.
- [x] `select([])` returns the always-on jobs without raising.
- [x] `select(list(CLASSES))` returns every job (`10/10`).
- [x] The new tests are red (`DID NOT RAISE`) against the old `select()` and green after the guard.
- [x] `tests/test_ci_scope.py` and `make issue-bot-gates-check` stay green; no workflow or caller
      change.
- [x] `make lint`, `make check-docs`, `make check-wiring`, `make openspec-validate
      NAME=ci-scope-select-guard` exit 0.
