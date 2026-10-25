# A failed run whose PR is already gone must not red the fix-bot's sweep

## Why

The fix-bot is triggered by a `workflow_run` of `CI` that concluded `failure`, and its `sweep` job resolves
that run back to a PR before deciding whether there is anything to repair. It does that with
`make auto-merge-resolve` — the resolution the *merge gate* uses, which is right about the answer and
wrong about the consequence here: for the merge gate **nothing resolving is a loud failure** (a green PR
must never be silently dropped), while for the fix-bot **nothing resolving is the ordinary case** — the PR
merged, was closed, or its branch was deleted between the run and the sweep.

Measured on issue #629, run `40207293399` (head `andyholst:fix/engine-gate-strict`, event
`workflow_run`):

```
[auto-merge-resolve] no open pull request for run 40207293399 (head andyholst:fix/engine-gate-strict)
                     - nothing to merge, and a green PR must never be silently dropped
make: *** [Makefile:808: auto-merge-resolve] Error 1
##[error]Process completed with exit code 2.
```

There was nothing to repair: `fix/engine-gate-strict` had already landed as PR #627. The sweep still went
red, and the run-failure reactor then filed #629 against the fix-bot — a failure the code invented. The
class repeats on every merge that lands while a `CI` failure report is in flight, and each instance costs
a reactor issue, a triage pass and a red run in the bot's history.

The same resolution already knows the difference between "the PR is gone" and "the read failed": it treats
a 404 body or an error line as *no answer*, and never invents a number. What is missing is a caller that
may say *"no PR, and that is an answer"*.

## What Changes

- **`scripts/resolve_run_pr.py`** — `resolve --allow-none`: when neither source resolves a number, the
  command prints that there is nothing to repair, writes `number=` (empty) to `$GITHUB_OUTPUT`, and exits
  **0**. Without the flag the behaviour is unchanged: loud exit 1 naming the run and the head, which is
  what the merge gate depends on.
- **`Makefile`** — `make fix-bot-resolve REPO= RUN_ID= HEAD_OWNER= HEAD_BRANCH=` is the fix-bot's one code
  path (added to `.PHONY`); its `##` help line says the empty answer is allowed.
- **`.github/workflows/fix-bot.yml`** — the sweep's resolution step calls `make fix-bot-resolve` instead of
  `make auto-merge-resolve`, and echoes what an empty answer means. With no PR from the failed run the
  sweep proceeds exactly as its scheduled form does: it picks the PR that deserves the bot, and does
  nothing when no PR qualifies.
- **`tests/test_resolve_run_pr.py`** — the empty answer is pinned end to end against a real fake `gh`:
  `--allow-none` exits 0 and writes an empty `number=` line with a message naming *nothing to repair*; the
  default still exits 1 and writes nothing; the Makefile target passes the flag; the fix-bot workflow calls
  that target and no longer calls `auto-merge-resolve`; and `auto-merge.yml` still calls the strict one, so
  the merge gate cannot inherit the lenient behaviour.

## Impact

- A failed `CI` run whose PR has already landed ends the fix-bot sweep as a clean no-op instead of a red
  run, so the reactor files no issue for it.
- The merge gate is untouched: it keeps failing loudly on an unresolved run.
- No new dependency and no second code path — one resolver, two documented answers for the one question
  that differs between its callers.
