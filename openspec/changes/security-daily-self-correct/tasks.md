# security-daily-self-correct — tasks

- [ ] 1. `.github/workflows/security-scan.yml` — drop the `pull_request:` and `push:` triggers; the pipeline is its own daily `schedule` + `workflow_dispatch`
- [ ] 2. `data/security-policy.json` + `scripts/security_scan.py` — `enforce_events`, `verdict(event=…)`, report-only outside it
- [ ] 3. `make check-security-scan` fails on a re-added `push`/`pull_request` trigger, an empty/unknown/over-broad `enforce_events`
- [ ] 4. `scripts/security_bumps.py` — `floors` (maximum of the minimums), `plan`, `apply` (floors -> `make -C tools generate-requirements*` -> fast gates -> one PR), `check`
- [ ] 5. `tools/security-floors.in` exists and `-c security-floors.in` is included by `tools/requirements.in` and `tools/requirements-dev.in`
- [ ] 6. One PR on `fix/security-floors` with Issue/Fix/Benefit/Technical and `closes #<n>` per matched issue; an unsatisfied floor opens no PR
- [ ] 7. `renovate.json` (pip_requirements, pip-compile, dockerfile, github-actions, grouped, no top-level automerge) + `docs/RENOVATE.md` (closes #718)
- [ ] 8. Make targets `security-bumps-plan`, `security-bumps`, `check-security-bumps`; `.PHONY`, gate in `ci-unit`, classified in `scripts/issue_bot_gates.py`
- [ ] 9. `tests/test_security_bumps.py`, `tests/test_renovate_config.py`, and the updated `tests/test_security_scan.py` all green under `make test-unit`
- [ ] 10. `docs/SCANS.md` + `README.md` docs table + `agent-wiki/2026-10-27-security-daily-self-correct.md` + `CHANGES.md` row
- [ ] 11. `make check-wiring check-docs check-workflows check-security-scan check-security-bumps lint` green and `make openspec-validate NAME=security-daily-self-correct` passes
