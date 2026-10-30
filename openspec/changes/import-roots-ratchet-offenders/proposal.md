---
name: import-roots-ratchet-offenders
about: The import-roots ratchet names the file and line of every site its rule counted
status: active
---

# Name the offending site when the import-roots ratchet reds (issue #1066)

## Proposal

`scripts/check_import_roots.py ratchet` — the CI gate `make check-import-roots` — refuses a tree whose
count of a rule rose above `tests/fixtures/import-roots-baseline.json`, and prints only the aggregate:

```
[import-roots] bare: 53 now, 52 recorded — the migration may only shrink this count (issue #796); a new file adding its own root is refused here
```

The same script already knows the answer: `report` (and `check`) print each finding as `tests/…:line`
from `findings()`. `ratchet` throws that away and hands the reader a number, so the person whose PR
went red has to re-run the guard to learn which file they added — the "name the mechanism, don't make
the reader re-derive it" complaint filed as #1066 (the same shape as #1053's stale census pointer).

## Motivation

Measured at `main@36cfa8c1`: the ratchet is green (`{'sys-path': 32, 'bare': 52, 'syntax': 0}`
against a baseline recording the same), so a red is always caused by the author's own new file. Every
other message the gate can produce names its culprit; this one — the only one an author actually
hits — names the fixture instead of the file.

## Change

- `scripts/check_import_roots.py`: each over-count item carries `over` (how far past the recording)
  and `sites` (the `file:line` of every finding of that rule, from the same `findings()` output
  `report` prints); a new `render_ratchet()` prints the aggregate line plus one line per site. The
  exit code (`1` on any item) and the refusal semantics are unchanged, and a missing-baseline item
  still prints as before.
- `tests/test_import_roots.py`: behaviour tests over a real scratch tree — a planted root reds naming
  that exact `file:line`, removing a root stays green, and no extra root keeps the command green and
  silent about sites. The tests assert the named site, never the whole message string.
- `agent-wiki/` note + `docs/changes.d/` fragment.

## Acceptance

- [ ] With an extra root planted, `python3 scripts/check_import_roots.py ratchet` exits 1 and its
  output names that file and line.
- [ ] With the tree at or below the baseline, the command exits 0 and prints no site list.
- [ ] `report` output and the `check` exit-code contract are unchanged.
- [ ] `make check-import-roots`, `make lint`, `make check-docs`, `make check-wiring`,
  `make openspec-tasks-check` and `make test-unit` exit 0.
