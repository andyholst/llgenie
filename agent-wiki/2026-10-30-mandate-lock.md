# Author mandate lock (issues #976/#988/#1031, PR #1033)

What was verified: `tests/test_pr_authors.py` carries a regression lock asserting the author
rule keeps the post-#840 wording —

- `AGENTS_MANDATE` equals `## A PR's commits are authored through an allowed email — no one else`
  (the shipped string, not the older exact-pair "by Andy Holst or Asimov Agent — no one else")
- `AGENTS.md` carries "The EMAIL is the gate" and "they PASS" (not "they FAIL")

It reds the tree the moment the #977 author-gate revert hunk (which had restored the old wording
as a doc-vs-code contradiction) lands. Verified: `pytest tests/test_pr_authors.py` → 29 passed
including the lock.

Spec / issue / PR: issues #976, #988, #1031; PR #1033.
