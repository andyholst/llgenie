# pin-github-actions — tasks

- [x] 1. `scripts/pin_actions.py` with `check` / `report` / `update` (stdlib-only for check/report)
- [x] 2. Every third-party `uses:` in `.github/workflows/**` and `.github/actions/**` rewritten to a full commit SHA, tag kept as a comment
- [x] 3. `make check-actions` / `actions-report` / `update-actions` targets, declared `.PHONY`, `check-actions` wired into `make ci-unit`
- [x] 4. `tests/test_pin_actions.py` (fixture rules + the real tree fully pinned), passing in `make test-unit`
- [x] 5. `docs/SECURITY.md` written and linked from `README.md`; `make check-docs` green
- [x] 6. `make check-actions` exits 0 on the branch and non-zero on `main`; `make check-workflows` green; `make check-wiring` green
