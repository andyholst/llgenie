# rebase-bot-skill-comma — proposal

Issue: [#641](https://github.com/asimov-agent/llgenie/issues/641)

## Why

`rebase-bot` is the only thing that unsticks a PR whose files moved under it, and it cannot run: its
agent leg inlines the `hermes …` command inside `$(call scrubbed_run,…)` (it must — the container's
`Makefile` is the conflicted file, issue #460), and that command carried a literal comma in
`-s rebase-conflict,bot-unattended`. GNU make splits `$(call)` arguments on commas in the unexpanded
text, so everything after `-s rebase-conflict` was dropped, the shell saw an unclosed quote, and the
leg exited 2 (`unexpected EOF while looking for matching '`) before the agent started. Measured on
run 40212644476: #602 and #605 were left `DIRTY`, "agent failed", rebase aborted.

## What Changes

- **`Makefile`** — `REBASE_BOT_SKILLS := rebase-conflict,bot-unattended` and the leg references
  `$(REBASE_BOT_SKILLS)`, so no literal comma reaches `$(call …)`. A comment states the rule where the
  next leg author will read it.
- **`tests/test_agent_legs_quoting.py`** (new) — expands **every** leg wrapped by
  `$(call scrubbed_run,…)` with `make -n`, and fails on an odd number of single quotes (a truncated
  command) or a `-s` list that lost its second skill. The check reads the expanded recipe, because
  that is what the shell receives.
- **`README.md`** — the rebase-bot section names the trap and the variable.

Not covered: #602 / #605's own content (e.g. the strata Hub-flag byte-stability test), filed
separately.

## Benefit

Conflicted PRs get rebased again — the actual blocker behind two engine-bump PRs sitting red for
hours — and the failure mode cannot come back silently, because a leg that loses half its command is
a red test rather than a runtime surprise.
