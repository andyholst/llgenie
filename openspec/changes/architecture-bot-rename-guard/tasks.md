# Tasks — architecture-bot-rename-guard

- [x] 1. OpenSpec change
- [x] 2. `scripts/module_name_guard.py`: the rule once (regex, allowed prefixes, `offenders`,
      `is_clean`, `hits`, `check` CLI)
- [x] 3. `tests/test_rename_llgenie_serve.py` imports it (reviewer and writer share one function)
- [x] 4. `scripts/architecture_bot.py`: `publish()` refuses a doc that names the retired module before
      any write; `brief()` states the rule without spelling it
- [x] 5. `tests/test_architecture_bot.py` + guard unit cases
- [x] 6. README + agent-wiki
- [x] 7. Verified: `pytest tests/test_architecture_bot.py tests/test_rename_llgenie_serve.py` → 30 passed
