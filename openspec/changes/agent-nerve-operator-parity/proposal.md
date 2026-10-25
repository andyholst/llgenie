# agent-nerve-operator-parity — proposal

Issue: [#611](https://github.com/asimov-agent/llgenie/issues/611)

## Why

The bots' agent image runs the nerve plugin on the `lean` profile with `gate_mode: off`, while the host this
repo's bots are modelled on runs `operator` with the gate in `advisory`. That is not a cosmetic difference:
for a **named** profile the module set comes verbatim from `hermes_nerve/profiles.py`
(`modules = dict(PROFILES[name])`), and the only later pass that reads settings can switch a module **off**,
never on. So the image wrote four settings for modules its profile never registers:

```
[nerve-profile] profile 'lean' does not register every module these settings need:
  - gate_mode='advisory' needs module 'action_gate' … the setting would be inert
  - context_engine_mode='apply' needs module 'context_governor' … inert
  - context_curation_mode='apply' needs module 'context_governor' … inert
```

Measured against the installed plugin's own `PROFILES` table (v0.3.1). In other words: the context curation
the script calls "where prompt tokens are won" never ran, the pre-tool decision could not fire, and
`local_learning` was off — the layer was configured on paper and off in the run, with nothing visibly
broken, which is exactly the failure mode the JEV integration exists to avoid.

## What Changes

- **`scripts/install_nerve_ci.sh`**: the image is built with the host's profile and gate —
  `HERMES_NERVE_PROFILE` default `operator`, `HERMES_NERVE_GATE_MODE` default `advisory` — writes
  `nerve_profile` (the host carries it in the settings as well as the sidecar), `gate_scope: all` and
  `allow_tool_override false`, and keeps `work_supervision_mode` at `shadow` because `operator` does not
  register `work_supervision` (a non-shadow mode there asks a module that is off). Its verifier covers the
  new keys.
- **`scripts/nerve_profile_check.py`** (new): the rule, once — a setting that only matters when its module is
  registered (`gate_mode`→`action_gate`, `context_engine_mode`/`context_curation_mode`→`context_governor`,
  `work_supervision_mode`→`work_supervision`, `nervous_enabled`→`nervous`) must have that module enabled by
  the chosen profile. The build runs it against the **installed** plugin's `PROFILES` table and fails on a
  mismatch, printing the resolved module set.
- **`containers/agent/Dockerfile`**: the ARG docs and defaults say `operator` / `advisory` / `shadow`, and
  the checker is COPYed in; **`scripts/ci_images.py`** carries it as a hash input, so changing the check
  moves the image tag.
- **`Makefile`**: `make nerve-profile-check` runs the rule's both-directions self-test, so `make test-unit`
  locks it without a plugin install (`--self-test`; the build path uses the real table).
- **Tests** (`tests/test_agent_nerve.py`): the image's profile/gate/settings are the host's; `operator`
  accepts them and `lean` is rejected naming `action_gate` and both curation settings; the Dockerfile COPY,
  the ci_images hash input and the make target are wired. The build-time tests' expectations move from
  `lean`/`off` to `operator`/`advisory`, and the plugin stand-in gains the `PROFILES` table the build reads.
- **`README.md`** and **`agent-wiki/2026-10-25-agent-nerve-operator-parity.md`**: what the image runs and why.

## Not covered

- Persisting `local_learning` across runs: the bot container is `--rm`, so what it learns dies with the run.
  Durable state (a mounted directory) is its own change with its own evidence.
- `work_supervision` for bots: `operator` does not register it. Running it needs a profile that does
  (`lean`/`marie_kondo`) and a policy decision; filed separately if it comes up.
- The plugin pin and the provider: unchanged (`keeltrace/hermes-nerve@v0.3.1`, `typesafe`, `jev-latest`).

Refs: #238 (the JEV layer and its host wiring), #359 (the redacted preflight), #585 (the `laya` extra), #601.
