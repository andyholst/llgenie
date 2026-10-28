# issue-dedupe-jev-preflight — proposal

Issue: [#802](https://github.com/asimov-agent/llgenie/issues/802)

## Why

A bot leg's credential has two ends, and only one of them was gated. `scripts/require_env.py` makes a
leg **refuse** to start on a missing key (issue #363), and the suite derives the leg roster from the
Makefile — but nothing compared a leg's required keys against the `env:` of the job that CALLS it. So
a guard can kill the run it was meant to protect:

- `issue-dedupe.yml`'s `dedup` job carried `NOUS_API_KEY` and `REPO` only, while
  `make agent-jev-preflight NERVE_REQUIRE=1` opens with `scripts/require_env.py TYPESAFE_API_KEY`.
- Measured on `main` (`464fee5`): run `40702295009` (14:04:02Z), job `122867360526`, step
  *"Prove the JEV engine is active"* →
  `[require-env] FATAL: TYPESAFE_API_KEY is missing or empty — refusing to start` →
  `make: *** [Makefile:661: agent-jev-preflight] Error 2`. The pick had already chosen a pair
  (`canonical=782 copy=783 at 0.92`), so the sweep retired **nothing**; the same step failed on the
  13:34:15Z schedule run (`40697636784`) and the last green run was 06:20:04Z (`40643207518`).
- The preflight step is `if: steps.pick.outputs.picked == 'true'`, so the hole was invisible on every
  run that found no pair: a dead sweep looked exactly like a sweep with nothing to do.
- `registry-sync-review.yml` carried the identical hole in its `review` job, latent behind
  `if: steps.brief.outputs.action == 'review'` — it fires the moment a sync PR is green.

The #364 rule ("every key a leg forwards is SET by the job that calls it") could not see this: it
checks the keys a leg forwards with `-e`, on a hand-kept four-workflow roster, and the preflight's
required key is not a forwarded key on the dedupe leg (the leg forwards `NOUS_API_KEY`; the
*preflight* requires `TYPESAFE_API_KEY`).

## What Changes

- **`.github/workflows/issue-dedupe.yml`**: `TYPESAFE_API_KEY: ${{ secrets.TYPESAFE_API_KEY }}` on the
  `dedup` job env, with the measured run id and the reason in a comment.
- **`.github/workflows/registry-sync-review.yml`**: the same line on the `review` job env (the
  identical defect, one `if:` away from firing).
- **`tests/test_agent_shell_keys.py`**: a derived rule — which make targets are agent legs and the
  keys each one's `require_env.py` line demands (from the Makefile), and which job calls which leg
  (from every workflow file) — plus a planted-defect case that proves the rule catches #802's shape.
  Scope reuses #364's `_step_sets_key`: the job `env:` or that step's own `env:` counts, a sibling
  step's does not.
- **`docs/BOTS.md`**: the "#363" section documents the other end of the guard, with the run id.
- No change to the guard, to any leg, or to what any bot is allowed to do: this only stops a run from
  being killed by its own preflight.

## Impact

- Affected capabilities: `bot-credential-scope` (new).
- Affected specs: none modified.
- Two workflows gain one secret each (`TYPESAFE_API_KEY`, already a repository secret — set
  2026-10-14, used by `issue-bot.yml`, `fix-bot.yml`, `issue-refiner.yml`, `rebase-bot.yml`,
  `architecture-bot.yml`).
- `make test-unit` gains one assertion family over 14 guarded legs / 29 leg calls in 9 workflows.

## Not covered

- Re-enabling `issue-dedupe` (or `registry-sync-review`): both are `disabled_manually` since the 15:50Z
  sweep, tracked as #902 — an owner decision, not this change. A green run therefore cannot be cited.
- The hand-kept `BOT_JOBS` and `entries` rosters that #364 still uses for the `-e` forwarding half: they
  cover 4 of the 9 workflows that call an agent leg. Filed as its own work item, #908, linked back to
  this issue.
