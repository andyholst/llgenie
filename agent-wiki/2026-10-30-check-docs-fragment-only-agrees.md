# One contract for a fragment-only change (#1100)

Issue #1100: `scripts/check_docs.py check` and `tests/test_check_docs.py` answered different
questions. A change that follows the repository's own rule — add `agent-wiki/<note>.md` and
`docs/changes.d/<note>.md`, never edit `CHANGES.md` (issues #934, #1063) — passed `make check-docs`
and red `ci-unit`.

## Measured, at `main@6d118a03`

A fragment-only change was planted (a note + one-row fragment, `CHANGES.md` untouched):

```
make check-docs            -> exit 0  ([check-docs] ok: … CHANGES.md links no missing note …)
pytest test_check_docs.py test_changes_index.py
  FAILED test_the_real_tree_documents_every_user_facing_target
  FAILED test_the_real_index_renders_the_committed_changes_md
  2 failed, 21 passed
```

The run #1100 cites (PR #1091 at its superseded head `48f03bbf`, job `124314068669`) is the same
pair; at that PR's current head the two tests are green only because the PR regenerated
`CHANGES.md` alongside its fragment. The disagreement is real; the "blocked today" framing is not.

## Which side moved, and why

The tests moved. `scripts/changes_index.py:11` states the contract the gate is built on — *"It is
not a merge surface: the gate never requires it to be current, so a change PR never has to touch
it"* — and that is also what keeps two open PRs from conflicting. The CLI and `changes_index.py`
were already right; the suite asserted currency (`set(changes_links) == {every note}`,
`committed == rendered`) that the gate never promised.

## What the tests assert now

1. **membership, not currency** — every note has exactly one fragment, every fragment indexes a
   note that exists, and every row `CHANGES.md` carries is a row the renderer writes (a subset
   check, so the fragment tree can keep growing under it);
2. **the lag is reported** — the real-tree test accepts `— current` or `N row(s) behind`;
3. **the renderer stays the only author** — `write` determinism and idempotence are proven on a
   scratch tree, so no test edits the real `CHANGES.md` (a real-tree `write` in a lagging tree would
   edit it inside CI, exactly what #934 forbids);
4. **one behaviour test for the shape** — a note + fragment with an untouched `CHANGES.md` is green
   through both the library and the CLI, and a committed row naming a missing note is red in both.

## Sabotage loop

- fragment-only shape, **before** this change: `make check-docs` exit 0, the two tests `2 failed`.
- fragment-only shape, **after**: `make check-docs` exit 0, `25 passed`,
  `make changes-index-report` → `CHANGES.md: 267 row(s) committed, 268 rendered — 1 row(s) behind`.
- guard still bites: a committed row linking `agent-wiki/2026-10-30-gone.md` reds both tests and
  `make check-docs` (`[check-docs] ERROR: CHANGES.md: links agent-wiki/2026-10-30-gone.md, which
  does not exist`), restored afterwards.

OpenSpec change: `check-docs-fragment-only-agrees`. The landed scenario in
`changes-index-per-change-file` ("its output equals the committed `CHANGES.md`") contradicted the
requirement paragraph above it and is restated to the lagging-index contract with its test
reference. Delivered as the ready-for-review PR that closes #1100; merged only by the repository's
`auto-merge` job. Not covered: #1063, #934, #1101.
