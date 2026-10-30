# Two gates, one subject: the check that resembles the gate, and the head that outlived its report

Two lessons from the night of 2026-10-30, both recorded because each cost real time before it was
understood, and both share a shape: **a claim that was true of the thing measured, stated about a
wider thing.**

## 1. `check_docs` and `test_check_docs` check the same file to different depths

`scripts/check_docs.py check` returned **rc=0** on a change PR that added a `docs/changes.d/` fragment
and left `CHANGES.md` alone. From that we concluded — repeatedly, to several lanes — that a
fragment-only change was compliant with #678, and advised dropping the aggregate row. `ci-unit` then
failed on two tests:

```
tests/test_changes_index.py::test_the_real_index_renders_the_committed_changes_md
  assert committed == rendered, "CHANGES.md is out of date — run `make changes-index`"
tests/test_check_docs.py::test_the_real_tree_documents_every_user_facing_target
  assert set(info["changes_links"]) == {stem + ".md" for stem in info["wiki"]}
```

The CLI asks *"does `CHANGES.md` link a note that does not exist?"* — one-directional. The tests ask
*"does it link every note, and does the committed file equal the render?"*. Both are reasonable
questions; only the second gates, because only the second runs in `ci-unit`.

**The rule:** verify with the target CI actually invokes, and when a CLI and a suite share a subject,
quote which one produced the green. Filed as #1100, which also records that #1063's fragment-only
policy cannot be adopted until the tests are relaxed — otherwise the policy reds the suite.

**And the ordering detail**, found by doing it wrong: `CHANGES.md` is a shared append, so
`make changes-index` on a stale base produces a file that conflicts with main's. Rebase first, render
second.

## 2. A report outlives the branch it describes

A status line said a PR was `13/0/1` with its unit "running 17 min" at `48f03bbf`. By the time it was
read, that head had **concluded `failure`** at 21:27:28Z and the branch had already been fixed at
`d43f52b2`. Every number was genuinely measured; the photograph was simply of a superseded head.

The same class hit the planner from the other side: a board summary reported "nothing has failed
anywhere" because it was true of the heads just sampled, while a red head twenty minutes earlier was
still part of the board.

**The rule:** quote the head *and* its conclusion together, and where the conclusion is not yet
available say `pending at <time>` — a fact with an expiry rather than a state. Every aggregate
(`mergeable`, `mergeStateStatus`, `reviewDecision`) answers a different question from "did the gates
pass", so the only reliable read is `conclusion` per check-run, at a named sha.

## Why these are recorded here rather than in the body

Both are procedural rules a reviewer needs without a second lookup in the common case, but the
always-on set in `SKILL.md` is at its authoring limit (100,688 b). Splitting that body is #1095; until
it lands, lessons of this size live in `references/` and are cited from it.
