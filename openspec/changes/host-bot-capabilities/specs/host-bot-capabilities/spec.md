# host-bot-capabilities

## ADDED Requirements

### Requirement: Each host llgenie profile has an explicit toolset pin

The fixture `tests/fixtures/host-bot-capabilities.json` SHALL name the ten desktop profiles.
For each profile the cli toolset list SHALL be the shared base plus that profile's extras.
The list SHALL NOT contain `browser` or `computer_use`.

WHEN a profile config still enables `browser` on `platform_toolsets.cli`
THEN `check_config` reports that profile.

#### Scenario: a wide reviewer config is rejected

Given a reviewer config whose cli toolsets are only `browser`
When `check_config` runs against the fixture
Then the findings name `platform_toolsets.cli`.

- **Test:** `tests/test_host_bot_capabilities.py::test_check_flags_a_profile_that_still_has_browser`

#### Scenario: applying the pin removes browser and the force-push approval

Given a reviewer profile that still has `browser`, `computer_use`, and the force-push allowlist entry
When `apply_config` runs
Then the cli list equals the fixture pin, the force-push entry is absent, and a skill outside the keep list is disabled.

- **Test:** `tests/test_host_bot_capabilities.py::test_reviewer_pin_drops_browser_and_force_push`

### Requirement: Only the rebase lane keeps the force-push approval

`command_allowlist` SHALL contain the force-push entry for `llgenie-pr-merge-conflict` and for no other profile in the fixture.

WHEN the rebase profile is pinned
THEN the force-push entry remains.

#### Scenario: rebase keeps the approval

Given a config that already contains the force-push entry
When `apply_config` runs for `llgenie-pr-merge-conflict`
Then the entry is still present and `check_config` returns no findings.

- **Test:** `tests/test_host_bot_capabilities.py::test_rebase_lane_keeps_the_force_push_entry`

### Requirement: The host skills state the same pin

`llgenie-engine-improver` and `llgenie-architecture-pass` SHALL contain the `host-bot-tools` marker.
The engine skill SHALL name `code_execution`. The architecture skill SHALL name `web`.

WHEN the marker is inserted twice
THEN it appears once.

#### Scenario: the marker is idempotent

Given a skill body and the architect tool block
When `insert_tools_block` runs twice
Then the begin marker appears once and the block names `web`.

- **Test:** `tests/test_host_bot_capabilities.py::test_tools_block_is_idempotent_and_names_the_pin`

#### Scenario: the committed host skills carry the marker

Given the two HOST skills in `.hermes/skills/`
When their text is read
Then each contains the marker and issue `#1038`.

- **Test:** `tests/test_host_bot_capabilities.py::test_repo_host_skills_carry_the_marker`
