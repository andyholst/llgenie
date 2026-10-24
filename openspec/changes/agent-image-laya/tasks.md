# Tasks — agent-image-laya

- [x] 1. `scripts/install_nerve_ci.sh`: install with `--no-deps` (no `--yes-deps`), drop the `laya` extra from the installed `pyproject.toml` with a loud failure when it is absent, then `hermes plugins enable nerve`.
- [x] 2. `tests/fixtures/fake-hermes/hermes`: `plugins enable` exists and works; `plugins install` writes a `pyproject.toml` carrying the real `laya` extra.
- [x] 3. `tests/test_agent_nerve.py`: the install call never carries `--yes-deps`; the extra is dropped and the plugin enabled; the drop step fails loudly on a pyproject without it.
- [x] 4. A REAL image build proves it: `python3 scripts/ci_images.py ensure agent` exits 0 and the image passes `make agent-jev-preflight` (or the built image's own arrival proof).
- [x] 5. README + `agent-wiki/2026-10-24-agent-image-laya.md` describe the three-step install and name #585 / the PR.
- [x] 6. `make test-unit` green and `make openspec-validate NAME=agent-image-laya` exits 0.
