# 2026-10-27 — the bot turns one auto-fixable issue into one green PR, or nothing

Issue #717 (parent #713, blocked by #716). Branch `feat/security-bot`, cut from
`feat/security-issues` because it parses the body format that change writes.

## What was verified

- `make check-security-bot` → `OK: selects security, vulnerability, auto-fixable; pins from
  tools/requirements.in, tools/requirements-dev.in; container findings are refused, not guessed`.
- `tests/test_security_bot.py` → 11 passed. The whole chain runs for real: the body is parsed from
  the issuer's text, the pin is edited in a real file, the commit is pushed to a **real bare
  `origin`**, and `make` in the fixture root either succeeds or fails so "red gate ⇒ no PR" is the
  code's decision, not a mocked return. Only `gh` is a recording stub.
- `make check-docs` / `check-wiring` / `check-dispatch-forms` / `check-workflows` green.

## Decisions

- **Deterministic, no Hermes leg.** Once an issue carries a fixed version there is no judgement to
  make; a skill wrapping `make security-bot` would be an empty wrapper. The findings that DO need
  judgement are exactly the ones the bot refuses.
- **Green or nothing, enforced in code**: the fast gates (`lint`, `check-wiring`, `check-docs`,
  `check-security-scan`) run before the push; a red gate reverts the edit and comments the real
  output on the issue. A red PR is worse than no PR.
- **Refusal over guessing.** A `component:container` advisory is a base-image/scanner bump (a
  reviewed change), and a package pinned nowhere is not the bot's to invent.
- **The branch names the advisory** (`fix/security-cve-2024-1-numpy`), so `git branch` reads as a
  list of remediations — the marker's advisory field is parsed, not a substring of the raw comment.
- **Only `.in` files are edited**; the compiled `.txt` is regenerated. The same rule as Renovate
  (#718) and the same rule AGENTS.md states for humans.

## Status

Implementation complete on the branch; the PR opens once #716 (and #715/#714 before it) merge.
