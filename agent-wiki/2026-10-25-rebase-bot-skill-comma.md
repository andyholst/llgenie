# 2026-10-25 — rebase-bot's agent leg lost half its command to a comma

Issue: [#641](https://github.com/asimov-agent/llgenie/issues/641)
OpenSpec: `openspec/changes/rebase-bot-skill-comma`
Unblocks: [#602](https://github.com/asimov-agent/llgenie/pull/602), [#605](https://github.com/asimov-agent/llgenie/pull/605)

## What was wrong

`rebase-bot` reported "agent failed" on every conflicted PR. The cause was not the conflict:

```
/usr/bin/bash: -c: line 1: unexpected EOF while looking for matching `''
make[1]: *** [/tmp/tmp.EKglcReztW:360: rebase-bot-agent] Error 2
```

`rebase-bot-agent` is the one leg that inlines its `hermes …` command inside `$(call scrubbed_run,…)`
(it cannot use a `_<leg>` target: the container's `Makefile` is the conflicted file, issue #460). That
command carried a literal comma in `-s rebase-conflict,bot-unattended`, and `$(call …)` splits its
arguments on commas in the unexpanded text — so `$(1)` ended at `-s rebase-conflict`, the rest of the
command (including its closing quote) was dropped, and the shell exited 2 before the agent started.

`make -n rebase-bot-agent` on `2134cd8` printed exactly that truncated command.

## What changed

- `Makefile`: `REBASE_BOT_SKILLS := rebase-conflict,bot-unattended`, referenced as
  `-s $(REBASE_BOT_SKILLS)` inside the call, with a comment stating the rule where the next leg author
  reads it. No other leg is affected — their comma lives in a separate `_<leg>` target the container
  runs (`bash -lc 'make _issue-refiner'`).
- `tests/test_agent_legs_quoting.py`: derives **every** target whose recipe calls `scrubbed_run` from
  the Makefile, expands it with `make -n`, and fails on an odd number of single quotes; a second case
  pins `-s rebase-conflict,bot-unattended` on the rebase leg, a third pins the variable.
- `README.md`: the bot-leg table section names the trap and the variable.

## Verified

- On the fixed tree: `make -n rebase-bot-agent` → 2 single quotes, `-s rebase-conflict,bot-unattended`
  → `3 passed`.
- On the **pre-fix** Makefile (`git checkout -- Makefile`): the same test file → **3 failed**, so the
  test detects the defect rather than describing it.
- Gates: `make openspec-validate NAME=rebase-bot-skill-comma`, `make check-agent-skills`,
  `make check-wiring`, `make check-docs`, `make lint`.

## Status

Fix and test are in place; the PR references #641. #602/#605 still need their own content questions
(the strata byte-stability test that pins the old pin's data shape is a separate issue), but they can
now be rebased onto main at all.
