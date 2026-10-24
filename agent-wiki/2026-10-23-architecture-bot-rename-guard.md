# The rename rule reaches the writer

Issue: #573. PR: (opened with this change).

PR #572 (the architecture bot's doc refresh) went red on both unit jobs with
`tests/test_rename_llgenie_serve.py::test_no_live_file_mentions_the_old_module_name` — the regenerated
`docs/ARCHITECTURE.md` had added `llama_serve.py (deprecated alias of llgenie_serve.py)` to its module
table, and the rename guard (#251) refuses that spelling in any live file.

The rule existed only in the test, so the bot could not know it and nothing checked its output before it
committed. It now lives once, in `scripts/module_name_guard.py`: the test imports it, `publish()` runs
`offenders()` on the regenerated doc before any GitHub call or `git` write and refuses loudly, and
`brief()` states the rule to the agent without spelling the forbidden name (the brief is a live file too).

Verified: `pytest tests/test_architecture_bot.py tests/test_rename_llgenie_serve.py` → 30 passed,
including the refusal (no gh call, no branch, no commit) and the brief check.
