# Host llgenie bots pin their tools and skills

Issue #1038. The ten desktop profiles shared one config: no `platform_toolsets` pin, about 98
skills loaded on every lane, and a force-push approval on the reviewer as well as the rebase
lane.

The pin lives in `tests/fixtures/host-bot-capabilities.json`. `scripts/host_bot_capabilities.py`
writes `platform_toolsets.cli`, `skills.disabled`, the allowlist, and `kanban.orchestrator_profile`
(`llgenie-planner`). The two HOST skills carry the same list in a `host-bot-tools` block.

SOUL files stay as they are. Removing the copied fleet block is #1006. The PR-watch
`actions/runs/null/jobs` failure is #1037 and is fixed on the host profile, not in this tree.

Verified by `tests/test_host_bot_capabilities.py` against a fake profile tree. The live home is
applied by the same module and is not read by the unit test.
