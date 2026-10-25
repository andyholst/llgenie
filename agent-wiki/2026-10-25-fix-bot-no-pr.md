# 2026-10-25 — a failed run whose PR already landed is not a fix-bot failure

Issue: [#629](https://github.com/asimov-agent/llgenie/issues/629)
PR: _this branch_
OpenSpec change: `fix-bot-no-pr`

## What was red

The fix-bot's `sweep` job, on the `workflow_run` path, resolved the failed `CI` run's PR with
`make auto-merge-resolve` — the resolution the **merge gate** uses. Run `40207293399` had fired for head
`andyholst:fix/engine-gate-strict`, which had already landed as PR #627:

```
[auto-merge-resolve] no open pull request for run 40207293399 (head andyholst:fix/engine-gate-strict)
                     - nothing to merge, and a green PR must never be silently dropped
make: *** [Makefile:808: auto-merge-resolve] Error 1
##[error]Process completed with exit code 2.
```

Nothing needed repairing: the branch was gone. The sweep went red anyway, and the run-failure reactor filed
#629 against the fix-bot — a failure the code invented, and one it repeats whenever a merge lands while a
`CI` failure report is in flight.

## Root cause

Two callers ask the same question and the answer means opposite things. For the merge gate an unresolved run
is a **defect** (a green PR must never be silently dropped). For the fix-bot's sweep an unresolved run is the
**ordinary outcome** — the PR merged, closed, or its branch was deleted between the run and the sweep. The
resolver already distrusted every non-numeric answer, so the information was there; there was simply no
caller that could say "no PR, and that is an answer".

## Fix

- `scripts/resolve_run_pr.py`: `resolve --allow-none` renders "neither source resolved a number" as an
  answer — stderr says *nothing to repair*, `number=` (empty) goes to `$GITHUB_OUTPUT`, exit **0**. Without
  the flag the behaviour is byte-identical to before: loud exit 1 naming the run and the head, no value
  written. One resolver, one flag, no second code path.
- `Makefile`: `make fix-bot-resolve` (with `--allow-none`) is the fix-bot's code path, in `.PHONY`, with a
  `##` help line; `make auto-merge-resolve` stays strict.
- `.github/workflows/fix-bot.yml`: the sweep's resolution step calls `make fix-bot-resolve`, then reads the
  empty answer back out of `$GITHUB_OUTPUT` and says so. With no PR from the failed run the sweep continues
  exactly as its scheduled form does: it picks the PR that deserves the bot, and does nothing when none does.

## Verification

- `tests/test_resolve_run_pr.py` (in `make test-unit`): the lenient answer exits 0 and writes `number=`; the
  lenient flag still reports a live PR as `number=506`; the strict path still exits 1 and writes nothing; the
  fix-bot workflow calls `make fix-bot-resolve` and no longer calls `auto-merge-resolve`; `--allow-none` is
  passed by the `fix-bot-resolve` recipe alone and never appears in `auto-merge.yml`. `10 passed`.
- End to end through make, against a fake `gh` that answers nothing (the measured #629 shape):
  `make fix-bot-resolve …` → `[fix-bot-resolve] … nothing to repair`, `rc=0`, `$GITHUB_OUTPUT` = `number=`;
  the same run through `make auto-merge-resolve …` → `rc=2`, output empty.
- `make openspec-validate NAME=fix-bot-no-pr`, `make lint`, `make check-workflows`, `make check-wiring`,
  `make check-docs` green on the branch.
