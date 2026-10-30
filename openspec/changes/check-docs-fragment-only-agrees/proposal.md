# One contract for a fragment-only change: the gate accepts, the suite must too

## Why

`docs/changes.d/` is the index (issue #934): a change adds `agent-wiki/<note>.md` **and**
`docs/changes.d/<note>.md`, and `CHANGES.md` is rendered from those fragments by
`make changes-index` — "no change PR writes CHANGES.md" (issue #1063). The documented gate says so in
one place: `scripts/changes_index.py:11`, *"It is not a merge surface: the gate never requires it to
be current, so a change PR never has to touch it."*

The test suite asked a different question. Measured at `main@6d118a03`, with a fragment-only change
planted (a note + its one-row fragment, `CHANGES.md` untouched):

```
$ make check-docs
[changes-index] ok: 268 fragment(s) index every agent-wiki/ note, and every fragment indexes a note that exists
[check-docs] ok: every one of the 269 user-facing make targets is documented in 8 doc(s) ...
exit 0

$ pytest tests/test_check_docs.py tests/test_changes_index.py
FAILED tests/test_check_docs.py::test_the_real_tree_documents_every_user_facing_target
FAILED tests/test_changes_index.py::test_the_real_index_renders_the_committed_changes_md
2 failed, 21 passed
```

So a PR that follows the rule passes the check an implementer is told to run and reds `ci-unit` on
assertions that demand the opposite (`set(changes_links) == {every note}`, `committed == rendered`).
Two answers to one question means one of them is folklore; here it also means the repository's own
rule cannot be followed without a red pipeline (it blocks #1063).

## What changes

The suite moves; the check does not. The CLI and `changes_index.py` already state the intended
contract, and the fragment-only shape is what keeps two open PRs from conflicting — so the tests
stop asserting that `CHANGES.md` is *current* and assert what the gate actually guarantees:

1. **membership, not currency** — every `agent-wiki/` note has exactly one fragment, every fragment
   indexes a note that exists, and every row `CHANGES.md` carries is a row the renderer would write
   (a stale index may lag; it may never disagree or invent);
2. **the lag is reported, never failed** — the real-tree test accepts `— current` **or**
   `N row(s) behind` from `changes_index.py report`, so the state is visible without gating a PR;
3. **the renderer stays the only author** — determinism and idempotent `write` are proven on a
   scratch tree instead of on the real checkout (a real-tree `write` in a lagging tree would edit
   `CHANGES.md` inside CI, which is exactly what #934 forbids);
4. **one behaviour test for the shape itself** — a note + fragment with an untouched `CHANGES.md` is
   green through both the library and the CLI (`scripts/check_docs.py check`), and an index row that
   links a missing note is still red in both.

Every assertion is a behaviour (exit code, membership), never a source spelling; the note/fragment
sets are compared as designed bijections, and the committed index's rows as a **subset** of the
render, so the tree can keep growing.

Not covered: #1063 itself (the rule change), #934 (the fragment mechanism), the import-roots ratchet
(#1101), and any workflow edit.

## Impact

- `tests/test_check_docs.py` — the real-tree assertion becomes a membership/subset check, plus one
  new behaviour test for the fragment-only shape.
- `tests/test_changes_index.py` — the real-tree test asserts the renderer's output is either the
  committed table or a superset of it, and the report names which; `write`/determinism move to a
  scratch tree.
- `openspec/changes/changes-index-per-change-file/specs/documentation-surface/spec.md` — the landed
  scenario "the committed table is the renderer's output" contradicts the requirement paragraph above
  it; it is restated to the lagging-index contract, with its test reference.
- `docs/ARCHITECTURE.md` — the gate's sentence gains the lagging-index rule.
- `agent-wiki/` note + `docs/changes.d/` fragment.
