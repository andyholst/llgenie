# issue-dedupe died at its own JEV preflight — the job never carried the key (#802)

**Date:** 2026-10-28
**Issue:** #802
**Branch / PR:** `fix/issue-dedupe-jev-preflight` (PR opened against `asimov-agent/llgenie:main`)
**Written against:** `main@464fee5`, `AGENTS.md` 1302 lines

## What was measured

`gh run list --workflow issue-dedupe.yml` showed the sweep green at 06:20:04Z and red on every run
after it. The failing job (`dedup`) stopped at one step, and the raw job log named the cause:

```
2026-10-28T14:10:43.7086074Z [require-env] FATAL: TYPESAFE_API_KEY is missing or empty — refusing to start.
2026-10-28T14:10:43.7122725Z make: *** [Makefile:661: agent-jev-preflight] Error 2
```

Run `40702295009` (14:04:02Z, `workflow_dispatch`), job `122867360526`. The pick step had succeeded
(`canonical=782 copy=783 at 0.92`), so the sweep had work to do and retired nothing.

Cause: the `dedup` job's env carried `NOUS_API_KEY` and `REPO` only, while the step
`make agent-jev-preflight NERVE_REQUIRE=1` opens with `python3 scripts/require_env.py
TYPESAFE_API_KEY`. The preflight step is `if: steps.pick.outputs.picked == 'true'`, so the hole was
invisible on the runs that found no pair — the bot looked healthy whenever it had nothing to do.

The same hole existed in `registry-sync-review.yml` (`review` job), latent: its preflight is behind
`if: steps.brief.outputs.action == 'review'`, so it fires only when a sync PR is green.

## What changed

1. `.github/workflows/issue-dedupe.yml` — `TYPESAFE_API_KEY: ${{ secrets.TYPESAFE_API_KEY }}` on the
   `dedup` job env, with the measured run id in the comment.
2. `.github/workflows/registry-sync-review.yml` — the same line on the `review` job env (the identical
   defect, one `if:` away from firing).
3. `tests/test_agent_shell_keys.py` — a derived rule: which make targets are agent legs and the keys
   each one's `require_env.py` line demands (from the Makefile), and which job calls which leg (from
   every workflow file). A job that runs a leg without the keys its guard demands fails
   `make test-unit`. Scope is #364's: job `env:` or that step's env, never a sibling step's.
4. `docs/BOTS.md` — the "#363" section now documents the other end of the guard, with the run id.

## Decisions

- **The roster is derived on both sides, never hand-kept.** The repo has already paid twice for a
  hand-kept workflow roster (#349, #301); the existing #364 test keeps a four-entry list, so the new
  rule reads the Makefile and every workflow file instead.
- **A step key is not the job's key.** `_step_sets_key` is reused unchanged, so a key a *sibling* step
  exports still does not satisfy the rule (#364's exact shape).
- **Both files are fixed in this change.** The new rule derives its own roster, so leaving the sibling
  workflow broken would red `ci-unit` on `main` the moment this lands.

## Verification (real output)

| Check | Result |
|---|---|
| the guard's own two paths | `env -u TYPESAFE_API_KEY python3 scripts/require_env.py TYPESAFE_API_KEY` → `FATAL … exit 2`; with the key set → `OK … exit 0` |
| the new rule on the UNFIXED tree (`git stash` of the two workflows) | `1 failed, 10 passed` — findings name `issue-dedupe.yml:dedup` and `registry-sync-review.yml:review` |
| the new rule on the fixed tree | `11 passed` in `llgenie/test:latest` |
| roster non-vacuity | 14 guarded legs, 29 leg calls across 9 workflows on `main@464fee5` |

## Not verifiable here

`issue-dedupe` and `registry-sync-review` are both `disabled_manually` (the 15:50Z sweep, tracked as
#902), so no run can be dispatched to prove the fix end to end. The fix is proven at the level the
run failed at — the guard's exit status and the workflow/env wiring the suite now enforces.
Re-enabling either workflow is the owner's decision (#902), not part of this change.
