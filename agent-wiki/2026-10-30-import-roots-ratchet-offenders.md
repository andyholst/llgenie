# 2026-10-30 — issue #1066: the import-roots ratchet names the file and line it counted

## What was wrong

`scripts/check_import_roots.py ratchet` — the CI gate `make check-import-roots` — refused a tree whose
count of a rule rose above `tests/fixtures/import-roots-baseline.json` and printed only the aggregate:

```
[import-roots] bare: 53 now, 52 recorded — the migration may only shrink this count (issue #796); a new file adding its own root is refused here
```

The same script already knew the answer: `findings()` produces every root as `tests/…:line`, and both
`report` and `check` print it. `ratchet` reduced that list to a number, so the author whose PR went red
had to run a second command to learn which file they had added — a gate withholding the fact it holds.

## What the change is

- `ratchet()` now carries `over` (how far past the recording) and `sites` (the `file:line` of every
  finding of that rule) on each over-count item, taken from the **same** `findings()` call the other
  two commands use — no second scanner, no second rule set.
- `render_ratchet()` prints the aggregate line, then one line per site. The exit code (`1` on any
  item) and the refusal semantics are untouched, and a missing-baseline item still prints its own
  line, because nothing was counted to name.
- `tests/test_import_roots.py`: four behaviour tests over a real scratch tree — a planted root reds
  and the output names that exact `file:line`; no extra root is green and prints no site line; a
  removed root is green (the count may shrink); `report` still lists findings and exits 0.

## Decisions

- **Name every site of the offending rule, not one "new" site.** The baseline records a COUNT, not a
  set, so the ratchet has nothing to diff against and cannot honestly say which site is new. The
  output says that in a word ("records a count, not a set") and lists them all — the author knows
  which file they wrote. Recording the sites in the fixture would give real precision and is exactly
  the "recording mechanism" that #1066 puts out of scope.
- **No cap on the list.** A cap would send the reader back to `report` for the tail, which is the
  complaint this change fixes; `check`/`report` already dump the whole list, so the volume matches
  what the gate prints everywhere else.
- **`render()` is untouched.** `check` and `report` share it, and their output and exit codes are part
  of the existing contract.

## Proof

Measured in this worktree on `main@36cfa8c1` (before = the old script, after = this branch):

- extra root planted in `tests/test_strata_download.py`:
  `make check-import-roots` → `RC=2` (make wrapping the guard's `1`), the aggregate
  `sys-path: 33 now, 32 recorded` **plus** `tests/test_strata_download.py:2` among the named sites;
- planted root reverted: `make check-import-roots` → `RC=0`,
  `[import-roots] OK: counts at or below the recorded baseline {'sys-path': 32, 'bare': 52, 'syntax': 0}`;
- the new naming test fails on the old script (`KeyError: 'sites'`) and passes on this one, so the
  test locks the behaviour rather than the message text.

Issue: #1066
