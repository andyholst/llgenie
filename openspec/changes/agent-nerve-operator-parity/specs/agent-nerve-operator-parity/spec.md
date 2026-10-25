# agent-nerve-operator-parity

## ADDED Requirements

### Requirement: the agent image runs the host's nerve profile and gate

The agent image SHALL be built with `HERMES_NERVE_PROFILE` defaulting to `operator` and
`HERMES_NERVE_GATE_MODE` defaulting to `advisory` — the profile and mode the host runs — and SHALL write the
profile into `plugins.entries.nerve.settings.nerve_profile` as well as the sidecar, plus
`allow_tool_override false` and `gate_scope all`, so the image's own config states what the run does.

WHEN the agent image's nerve defaults are read
THEN the profile is `operator`, the gate mode is `advisory`, and both are written where Hermes reads them.

#### Scenario: the image's defaults are the host's

- **Given** `scripts/install_nerve_ci.sh`, `containers/agent/Dockerfile` and the CI image inputs
- **When** the nerve defaults and the settings the build writes are read
- **Then** the profile default is `operator`, the gate default is `advisory`, the settings carry
  `nerve_profile` and `allow_tool_override: false`, and the build verifier asserts each one
- **Test:** `tests/test_agent_nerve.py::test_the_bot_image_runs_the_hosts_nerve_profile_and_gate`,
  `tests/test_agent_nerve.py::test_the_build_wires_the_hosts_settings_and_keeps_gate_mode_a_string`,
  `tests/test_agent_nerve.py::test_the_build_selects_the_hosts_profile_through_the_plugins_own_loader`

### Requirement: a setting whose module the profile does not register fails the build

A nerve setting only has an effect when the modules it needs are registered, and for a named profile the
module set comes verbatim from the plugin's `PROFILES` table — settings cannot switch a module on. The build
SHALL therefore verify, against the **installed** plugin's table, that every active setting's module is
enabled (`gate_mode` ≠ `off` → `action_gate`; `context_engine_mode`/`context_curation_mode` not
`shadow|off` → `context_governor`; `work_supervision_mode` ≠ `shadow` → `work_supervision`;
`nervous_enabled` → `nervous`), SHALL fail naming the setting, the module and the profile when it is not, and
SHALL print the resolved module set when it is.

WHEN the build's settings are checked against the selected profile
THEN every active setting has its module, or the build stops with the mismatch named.

#### Scenario: the host's profile accepts the settings the image writes

- **Given** the settings the build writes and the plugin's `operator` table
- **When** the parity rule runs
- **Then** it reports no findings and lists `action_gate`, `context_governor`, `local_learning`, `nervous`,
  `receipts`, `reflex` as the registered modules
- **Test:** `tests/test_agent_nerve.py::test_a_setting_without_its_module_fails_the_parity_check`

#### Scenario: the profile the image used to run is rejected

- **Given** the same settings and the plugin's `lean` table
- **When** the parity rule runs
- **Then** it names `gate_mode`→`action_gate` and both `context_*_mode` settings→`context_governor` as inert
- **Test:** `tests/test_agent_nerve.py::test_a_setting_without_its_module_fails_the_parity_check`

#### Scenario: a shadow or off setting asks nothing of its module

- **Given** `gate_mode: off` and `*_mode: shadow` with the `lean` table
- **When** the parity rule runs
- **Then** it reports no findings, because a mode that measures nothing must not demand its module
- **Test:** `tests/test_agent_nerve.py::test_a_setting_without_its_module_fails_the_parity_check`

### Requirement: the parity rule is exercised without a plugin install

`make nerve-profile-check` SHALL run the rule's both-directions self-test on synthetic profile tables — one
that enables every module a setting can need, one that does not — so `make test-unit` locks the rule's
behaviour without installing the plugin, and the build path uses the same code against the real table.

WHEN `make nerve-profile-check` runs
THEN the full table passes and the thin table fails naming each missing module.

#### Scenario: the self-test proves both directions

- **Given** the repository with no plugin installed
- **When** `make nerve-profile-check` (equivalently `python3 scripts/nerve_profile_check.py --self-test`) runs
- **Then** it exits 0 and prints `self-test OK`, having rejected a settings set on the thin table
- **Test:** `tests/test_agent_nerve.py::test_a_setting_without_its_module_fails_the_parity_check`
