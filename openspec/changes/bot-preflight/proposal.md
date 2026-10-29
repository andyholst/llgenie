# Bot preflight: fetch main, re-read the rulebook, cite it (issue #792)

## Why

A leg starts from whatever tree it is handed, and nothing proved it read the current `AGENTS.md`.
Two measured cases on 2026-10-28: the owner's checkout sat at `17cdcf3` while `origin/main` had moved,
and both host SOULs had been rewritten the same day with no record of which rulebook they obeyed.
The cost is a 60-minute implement run whose work the next gate rejects.

## What changes

- `scripts/bot_preflight.py` + `make bot-preflight`: fetch `origin/main`, fast-forward a clean behind
  checkout, refuse a dirty or diverged one naming its paths, and write `preflight.txt`
  (`main`, `agents_bytes`, `agents_lines`, `agents_headings`, `agents_headings_sha256`, and the
  `AGENTS: <sha> <bytes>b <lines>l` line a bot PR body must carry).
- `CHECK=1` re-derives the record and fails when `preflight.txt` disagrees with the tree it sits in.
- `bot-unattended`'s SKILL.md states the obligation; `make check-agent-skills` keeps it there.
- `docs/BOTS.md` names the target, so `make check-docs` stays green.

## What does not change

`rebase-bot`'s staleness sweep (#246) keeps PRs current; this makes the *start* of work current,
and neither replaces the other. The `AGENTS.md` half (#849) and the SOUL half (#866) are separate.
