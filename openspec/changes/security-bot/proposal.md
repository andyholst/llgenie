# security-bot — proposal

Issue: [#717](https://github.com/asimov-agent/llgenie/issues/717)
Parent: [#713](https://github.com/asimov-agent/llgenie/issues/713)
Blocked by: [#716](https://github.com/asimov-agent/llgenie/issues/716) (the issues it reads)

## Why

The scans file tagged issues with a fixed format (#716); nothing acts on them. A remediation bot
that opens a red PR is worse than no bot at all — it puts the repository in front of a reviewer with
work that does not pass its own gates.

## What Changes

- **`scripts/security_bot.py`** — `select` (oldest `security`+`vulnerability`+`auto-fixable`),
  `parse` (package and `current -> fixed` from the issuer's body; refuse rather than guess),
  `apply_plan` (the ONE line that owns the pin, in `tools/requirements*.in`), `apply` (edit → fast
  gates → branch → commit → push → `gh pr create`), `check` (the contract gate).
- **Green or nothing**: a red gate reverts the edit, comments the real output on the issue, and
  opens no PR. The bot never merges, never pushes to `main`, never force-pushes.
- **Refusals are explicit**: a `component:container` advisory (base-image/scanner bump — a reviewed
  change) and a package pinned nowhere the bot can see are commented, not guessed.
- **`.github/workflows/security-bot.yml`** — `issues: [labeled]`, a daily schedule and
  `workflow_dispatch`, with the repository's `guard` job first and a scoped permission set.
- **Make targets** `security-bot-pick`, `security-bot` (`DRY=1`), `check-security-bot`; the gate is
  in `make ci-unit`.
- **`docs/SCANS.md`** gained the bot section; `tests/test_security_bot.py` (11 tests) exercises the
  real parse, the real file edit, the real git push against a bare `origin`, and both gate outcomes.

## Not covered

- A Hermes agent leg: this bot is fully deterministic (no judgement is needed once the issue carries
  a fixed version), so a skill would be an empty wrapper. A finding that needs judgement is exactly
  the one it refuses.
- Transitive-dependency resolution: the scanner's fixed version is applied verbatim.
- Merging: CI's `auto-merge` job owns landing, as for every other PR.
