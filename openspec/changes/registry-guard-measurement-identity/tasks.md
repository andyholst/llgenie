# Tasks

- [x] 1. `openspec/changes/registry-guard-measurement-identity` — proposal + `specs/registry-guard/spec.md` (G/W/T, a `- **Test:**` line per scenario) + this checklist (issue #668)
- [x] 2. `scripts/registry_keys.py` — post identity (`/status/<id>`) across the whole store (`engines[]` + `engagement.seen_posts`); engine-level measurement loss; `drift()` for the re-read figures; `DERIVED_LISTS` so an emptied `seen_posts` placeholder is not ten key losses; measurements no longer keyed by the exact `(engine, hardware)` pair
- [x] 3. `tests/test_registry_keys.py` — every real loss still fails; each false-positive class passes (hardware relabel, profile→status URL, counter re-scrape, re-stated t/s, emptied placeholder, re-attributed post, demoted post, post gone store-wide); the CLI prints notes and exits 0; the vendored store is additive against itself
- [x] 4. `AGENTS.md` — the additive-only section states the narrowed rule (what fails, what is reported) instead of the old "lowered t/s / counter is a defect"
- [x] 5. `README.md` — the registry/guard section documents what `make check-registry-keys` fails on and what it prints as a note
- [x] 6. `agent-wiki/2026-10-26-registry-guard-measurement-identity.md` — the work record, referencing issue #668 and PR #671
- [x] 7. Verified against the real store: `python3 scripts/registry_keys.py --cur <upstream>/data/models.json` exits 0 with `OK: additive only — nothing lost` (106 models, 81 notes); the pre-change code exits 1 with 47 findings on the same pair
- [x] 8. Verified: `make lint`, `make check-registry-keys` (OK, 23 models, 0 notes), `make check-docs` (200 targets), `make check-wiring` (202 documents), `make check-pr-hygiene`, `make openspec-validate NAME=registry-guard-measurement-identity` (valid) and `make test-unit` (**5201 passed, 6 deselected in 1595.65s**) all exit 0
