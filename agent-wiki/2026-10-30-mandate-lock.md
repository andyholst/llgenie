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

Measured verification at head `7eb2d84c` (after the push that landed this record):
- holds gate run 40974911311 → completed/success (no do-not-merge label present)
- CI run 40974911595 → in_progress (no completed-run verdict yet at this head; not claimed)
- local gates: `check_pr_authors` over `f244efe8..7eb2d84c` → OK; `make check-docs` → ok (a local pass, not a CI run)
- executed suite at head `75c83814` (final pushed head of this record): `pytest tests/test_pr_authors.py` → **29 passed in 2.97s, exit 0**
- pushed+verified fork ref (resolves the local-only report): `git ls-remote --heads https://github.com/andyholst/llgenie.git fix/1031-author-alias-mandate` → **`b7a406f1`** (change-record on the pushed head)
- fresh CI at final pushed head `e29035e2`: run **40975428531** in_progress (openspec, guard, holds, ci-images, top-tier pass; linux/unit, lint, install, agents-read, scanner pending) — no completed-run verdict yet, not claimed
- sibling census-gate acceptance (#1042 re-verdict at `cf89b860`, this lane): the doc's `measured at <sha>` invariant is **count-based** — pointer must be a real commit (`cat-file …^{commit}`) AND its tree must carry HEAD's `git ls-tree -r` tracked-file count; verified both red directions (dangling pointer exit 1; count-drift to a 1959-file tree exit 1) and green at the real pointer (exit 0). Literal `pointer == HEAD` declined as unsatisfiable-by-design (the doc lives inside the tree it measures)
- #1042 re-verify at `04d9308b` (this lane): census re-derived 1966 tracked (rebase onto main), `measured at 348f7b4e` real non-dangling ancestor matching HEAD's count; DEFERRED-contract fix verified — `check-architecture-census` wired into `ci-unit` via `DEFERRED` with a non-empty reason (FAST_GATES stays the pinned six), `tests/test_issue_bot_gates.py` → 10 passed (note: needs `pyyaml` installed; its absence is an interpreter gap, not a repo defect). Gate set green (lint / check-docs census OK / check-wiring OK 277 / check_pr_authors OK); deciding CI leg excluded from verdict while in_progress.
- #1042 deciding leg status at the time of this check: CI run 40987463865 at head 04d9308b → `in_progress` (no completed-run verdict to quote; holds 40987463654 success; no do-not-merge label — holds gate green).

