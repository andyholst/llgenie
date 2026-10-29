# Bot preflight: fetch main, re-read the rulebook, cite it (#792)

A bot leg used to start from whatever tree it was handed. Two measured cases on 2026-10-28 made that
untenable: the owner's checkout sat at `17cdcf3` while `origin/main` had moved, and both host agents'
`SOUL.md` files had been rewritten the same day with nothing recording which rulebook they obeyed.

`make bot-preflight` now does the three things in the order that matters — `git fetch origin main`,
fast-forward a clean behind checkout (`--ff-only`, never a rebase), then measure `AGENTS.md` **at that
commit** rather than from the working tree. A dirty checkout is refused naming its paths; a diverged
one is refused with `ahead`/`behind` counts and the differing paths, and the leg's own commit is left
untouched, because a preflight that quietly rewrites history is worse than no preflight.

The record is `preflight.txt`: the `origin/main` sha, `AGENTS.md`'s byte size, line count, heading
count and a sha256 over its `## `/`### ` heading list, plus the one line a bot PR body carries —
`AGENTS: <sha> <bytes>b <lines>l`. The heading digest is the interesting field: editing a rule's
wording leaves it alone, adding or removing a rule moves it, so a reviewer can tell a prose edit from
a contract change without diffing 87 KB.

`CHECK=1` re-derives the record and fails when the file on disk disagrees with the tree, which is the
mode a CI step uses. `bot-unattended`'s skill states the obligation so a leg cannot be written that
skips it.

Measured at `464fee5`: 87,255 b / 1,302 lines, 35 headings, digest
`5b1351d1e456aebecf988c80da9bceed956222405d6d6693166e7964f1917380` — the same bytes and lines the
triage lane had been quoting by hand all evening.
