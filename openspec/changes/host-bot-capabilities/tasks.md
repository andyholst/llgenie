# Tasks

- [x] 1. Fixture names the ten profiles, their cli toolsets, the skills they keep, and the rebase-only force-push approval.
- [x] 2. `scripts/host_bot_capabilities.py` applies that fixture to a profile config and reports a finding when browser or a wrong force-push entry remains.
- [x] 3. Hermetic tests in `tests/test_host_bot_capabilities.py` lock the reviewer pin, the rebase exception, the tools-block insert, and the ten profile names.
- [x] 4. `.hermes/skills/llgenie-engine-improver/SKILL.md` and `.hermes/skills/llgenie-architecture-pass/SKILL.md` carry the `host-bot-tools` marker for their lane.
- [x] 5. `.hermes/skills/README.md` points at the fixture. The dated note and its `docs/changes.d/` row name issue #1038.
- [x] 6. `python3 -m pytest tests/test_host_bot_capabilities.py` exits 0, and `make openspec-validate NAME=host-bot-capabilities` exits 0.
