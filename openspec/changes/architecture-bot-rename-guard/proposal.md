# The rename rule reaches the writer, before it writes

## Why

`docs/ARCHITECTURE.md` is regenerated every 6 hours by the architecture bot. That refresh wrote the
retired CLI module's name into the module table:

```
| Product path | `llgenie_serve.py` (…), …, `llama_serve.py` (deprecated alias of `llgenie_serve.py`) |
```

`main` has no such mention. The rename guard (`tests/test_rename_llgenie_serve.py`, issue #251) refuses
that spelling in any live file — only the deprecated shim, `agent-wiki/` and `openspec/changes/` may carry
it — so PR #572 went red on **both** unit jobs (`1 failed, 5072 passed`, run `39996295998`), every other
check green, 25 minutes after the doc was pushed.

Two defects, one cause: the rule was stated **only in a test**, so (a) the bot had no way to know it, and
(b) nothing checked the regenerated doc before it was committed and pushed. Every 6-hourly refresh could
therefore reintroduce it, at ~40 runner-minutes of unit CI per occurrence, on a PR nobody is watching.

## What Changes

- **`scripts/module_name_guard.py`** (new) — the rule once: the regex, the allowed prefixes (the shim,
  `agent-wiki/`, `openspec/changes/`, itself), `offenders(text)` / `is_clean(text)` / `hits(root, …)` and
  a `check` CLI that names every offending file and exits 1.
- **`tests/test_rename_llgenie_serve.py`** — imports that rule instead of re-declaring it, so the reviewer
  and the writer cannot drift; its scan helper now shares the same skip lists.
- **`scripts/architecture_bot.py`** — `publish()` runs `offenders()` on the regenerated doc and refuses
  LOUDLY (no branch, no commit, no push, no PR) when it trips; `brief()` states the rule to the agent
  without spelling the forbidden name (the brief is itself a live file).
- **`tests/test_architecture_bot.py`** — a doc naming the retired module is refused before any GitHub
  call; the brief carries the rule and stays clean itself.
- **`README.md`**, **`agent-wiki/`** — the rule, and where it is enforced.

## Impact

- A drifted refresh fails in seconds with a message naming the doc, instead of a red PR 25 minutes later.
- The guard's rule exists once; changing it changes what both the bot and `make test-unit` enforce.
