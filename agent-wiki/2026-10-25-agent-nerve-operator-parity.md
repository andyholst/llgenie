# 2026-10-25 — the bot image runs the host's nerve profile, and the build proves it

Issue: [#611](https://github.com/asimov-agent/llgenie/issues/611)
PR: [#612](https://github.com/asimov-agent/llgenie/pull/612)
OpenSpec change: `agent-nerve-operator-parity`

## What was wrong

The host runs Hermes with nerve on `operator` and the action gate in `advisory`. The image the bots run was
built on `lean` with `gate_mode: off`, while still writing `context_engine_mode: apply`,
`context_curation_mode: apply` and `work_supervision_mode: advisory`. For a NAMED profile the module set
comes verbatim from `hermes_nerve/profiles.py` (`modules = dict(PROFILES[name])`), and the only later pass
that reads settings can switch a module **off** — so those settings were written for modules `lean` never
registers. Measured with the installed plugin's table (v0.3.1):

```
[nerve-profile] profile 'lean' does not register every module these settings need:
  - gate_mode='advisory' needs module 'action_gate' …
  - context_engine_mode='apply' needs module 'context_governor' …
  - context_curation_mode='apply' needs module 'context_governor' …
```

i.e. the context curation the script's own comment calls "where prompt tokens are won" never ran, the
pre-tool decision could not fire, and `local_learning` was off — configured on paper, off in the run, with
nothing visibly broken.

## What the image does now

- `operator` (reflex, nervous, **action_gate**, **context_governor**, receipts, **local_learning**), gate
  `advisory`, `gate_scope: all`, `allow_tool_override: false`, and `nerve_profile` written in the settings as
  well as the sidecar — the host's shape.
- `work_supervision_mode: shadow`, because `operator` does not register `work_supervision`; a non-shadow mode
  there would ask a module that is off to do something.
- `scripts/nerve_profile_check.py` runs **in the build** against the installed plugin's `PROFILES` table and
  fails it on any setting whose module the profile does not enable, printing the resolved module set. The
  same rule's both-directions self-test is `make nerve-profile-check`, so `make test-unit` locks it.

## Verification

- `tests/test_agent_nerve.py` — the image's profile/gate/settings are the host's; `operator` accepts them,
  `lean` is rejected naming `action_gate` and both curation settings; `shadow`/`off` demands no module; the
  Dockerfile COPY, the `ci_images` hash input and the make target are wired. The plugin stand-in gained the
  `PROFILES` table the build reads (`tests/fixtures/fake-nerve-plugin`).
- Falsified by running the checker against the fixture table: rc=0 for `operator` (6 modules), rc=1 for
  `lean` with the three findings above.
- `make nerve-profile-check` → `self-test OK: 5 rules, both directions (findings: 4)`; `make test-unit`,
  `lint`, `check-docs`, `check-wiring`, `check-workflows`, `check-dispatch-forms`, `check-pr-authors`,
  `openspec-validate` green.
- The image itself is built by CI (`agent-image-*`); the build now fails fast if the profile and the
  settings ever disagree again.

## Not covered

- `local_learning` does not survive a run: the bot container is `--rm`. Durable state is its own change.
- `work_supervision` for bots is a policy decision (needs a profile that registers it); filed separately when
  it comes up.
