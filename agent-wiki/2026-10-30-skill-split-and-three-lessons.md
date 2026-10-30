# The skill hit its authoring ceiling — split, then three lessons it could not previously accept

`agents/llgenie-pr-reviever/skills/software-development/llgenie-pr-review/SKILL.md` reached **100,688
bytes**, past `skill_manage`'s ~100,000-character ceiling. Above it, **every save is refused** with
`batch aborted, all touched skills rolled back` — and a refused save looks like a save, so the lesson
lands nowhere. That is how a lane can appear to keep forgetting lessons it keeps writing down: it is a
mechanism, not a discipline problem.

## The split

The largest self-contained section, `## Standing rules for this repo` — **628 lines, 59,349 bytes,
59% of the file** — moved verbatim to `references/standing-rules-for-this-repo.md`, with a one-line
pointer left at its heading.

Verified rather than eyeballed: every non-blank body line was checked against the reference and the
whole body compared for equality.

```
body lines: 628 · missing: 0 · exact match: True
SKILL.md: 100,688 b → 42,600 b
lint_linefeeds.py → LINT OK, exit 0
```

**The proof that the ceiling moved** is that the same `skill_manage` save which had been refused now
succeeds — and the entry recorded by it is *about the ceiling itself*. A lesson recorded through the
gate that was blocking it is the only direct evidence the gate opened.

## The three lessons it could then accept

**1 — test the merged result, not the merge.** A textual `merge-tree` can report zero conflicts while
the merged file is wrong: `committed == rendered` is a property of the result, not of the diff. After
`main` moved twice under an open PR, the merge was clean and the rendered aggregate stale — the merge
test caught what the merge did not.

**2 — an arm records a time, never a head.** Measured: `enabledAt 21:56:47Z` persisted across three
head moves, including one where the deciding gate had been cancelled and never ran. A reader sees
"armed at 21:56" and cannot tell which sha that referred to, nor that the arm predates the head it now
applies to. Contributes to #1106.

**3 — a red test is not always a complaint about the change.** Four reds were reported as symptoms of
a defect; at least one was the change's own safety check catching a duplicate that a verbatim
relocation is exactly the operation likely to create. The distinction is only visible in *which
assertion* fired, so read the assertion, not the count.

## Note on ordering

Split by **section**, never by concatenation: the reference is a verbatim copy of one heading's body,
so the diff is a move rather than a rewrite. The independent check is `missing: 0` over the body
lines, not a visual pass — an earlier split elsewhere in the fleet left two headings without a blank
line before them and `lint_linefeeds` caught both.
