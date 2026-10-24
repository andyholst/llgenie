# agent-image-install

## ADDED Requirements

### Requirement: The agent image resolves no optional extra it never uses

`scripts/install_nerve_ci.sh` SHALL install the nerve plugin without asking Hermes to resolve the
plugin's Python dependencies (`--yes-deps`), because that resolution is UNIVERSAL and the plugin's
optional `laya` extra (`laya==0.3.3` → `torch>=2.0.0`) has no solution for the
`python_full_version >= '3.14'` / `sys_platform == 'android'` marker split. It SHALL remove that one
extra from the installed copy and then enable the plugin, so the graph it resolves is satisfiable.

WHEN the build installs the nerve plugin
THEN `hermes plugins install` is called with `--no-deps` and never with `--yes-deps`, and the plugin
ends enabled.

#### Scenario: the install call never asks for dependency resolution

Given the install script as it is run by `containers/agent/Dockerfile`
When  its `hermes plugins install` invocation is read
Then  it carries `--no-deps` and carries no `--yes-deps`.

- **Test:** `tests/test_agent_nerve.py::test_the_build_installs_without_resolving_the_plugins_extras`

#### Scenario: the unused extra is gone from the installed copy and the plugin is enabled

Given a home with a fake `hermes` whose install writes the same `laya` extra the pinned plugin declares
When  the build half runs end to end
Then  the installed `pyproject.toml` no longer declares `laya`, and `plugins list --json` reports nerve `enabled`.

- **Test:** `tests/test_agent_nerve.py::test_the_build_drops_the_unused_laya_extra_and_enables_the_plugin`

### Requirement: Dropping the extra is asserted, never assumed

The extra-removal step SHALL fail the build, naming this decision, when the installed
`pyproject.toml` does not declare `laya` — a silent pass would turn a deliberate scoping into a
guess about what the next pin contains.

WHEN the installed copy carries no `laya` extra
THEN the step exits non-zero and its message says the decision must be revisited.

#### Scenario: a plugin without the extra fails the build loudly

Given an installed `pyproject.toml` whose optional dependencies carry no `laya` line
When  the removal step runs against it
Then  it exits non-zero and names the decision it could not apply.

- **Test:** `tests/test_agent_nerve.py::test_dropping_a_missing_extra_is_a_loud_failure`

### Requirement: The image's decision layer is still proven, hard

The build SHALL still refuse an image whose plugin is not admitted: the bundle file, the
`enabled … pinned@<sha8>` report, the profile sidecar read back through the plugin's own loader, every
`plugins.entries.nerve.settings.*` value, and the absence of a provider token remain assertions that
fail the build.

WHEN the plugin cannot be enabled or a setting does not read back
THEN the build fails.

#### Scenario: a plugin that is not enabled still fails the build

Given a home whose CLI reports the plugin as not enabled
When  the build half runs
Then  it exits non-zero and says nerve is not enabled.

- **Test:** `tests/test_agent_nerve.py::test_the_build_wires_the_hosts_settings_and_keeps_gate_mode_a_string`
