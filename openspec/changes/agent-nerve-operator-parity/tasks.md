# Tasks

- [x] 1. `scripts/install_nerve_ci.sh`: `HERMES_NERVE_PROFILE` default `operator`, `HERMES_NERVE_GATE_MODE` default `advisory`, `work_supervision_mode` default `shadow` (the profile does not register its module)
- [x] 2. The build writes the host's settings: `nerve_profile`, `allow_tool_override false`, `gate_scope all`, and its verifier asserts every one of them
- [x] 3. `scripts/nerve_profile_check.py`: the parity rule (`gate_mode`→`action_gate`, `context_engine_mode`/`context_curation_mode`→`context_governor`, `work_supervision_mode`→`work_supervision`, `nervous_enabled`→`nervous`), the build path reading the INSTALLED plugin's `PROFILES` table, and `--self-test`
- [x] 4. `containers/agent/Dockerfile`: ARG docs/defaults (`operator`, `advisory`, `shadow`), `COPY nerve_profile_check.py`, and `scripts/ci_images.py` carries it as a hash input
- [x] 5. `Makefile`: `make nerve-profile-check` (in `.PHONY`, with a help line, documented in README) runs the self-test
- [x] 6. Tests: the image's profile/gate/settings are the host's; `operator` accepts them and `lean` is rejected naming `action_gate` + both `context_*_mode` findings; the Dockerfile COPY, the hash input and the make target are wired; the plugin stand-in gains the `PROFILES` table
- [x] 7. Falsified against the installed plugin's table (v0.3.1): the rule exits 0 on `operator` (`action_gate, context_governor, local_learning, nervous, receipts, reflex`) and exits 1 on `lean` naming `gate_mode`, `context_engine_mode` and `context_curation_mode` as inert
- [x] 8. `README.md` + `agent-wiki/2026-10-25-agent-nerve-operator-parity.md`
- [x] 9. Gates green: `make test-unit`, `make nerve-profile-check`, `make lint`, `make check-docs`, `make check-wiring`, `make check-workflows`, `make check-dispatch-forms`, `make check-pr-authors`, `make openspec-validate NAME=agent-nerve-operator-parity`
