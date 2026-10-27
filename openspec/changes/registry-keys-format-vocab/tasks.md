# Tasks — registry-keys-format-vocab

- [x] 1. `scripts/registry_keys.py`: import `FORMAT_VOCAB` from `scripts/sync_registry.py`, add `_real_formats(row)`, and make the `formats` loss check a set difference over it.
- [x] 2. `tests/test_registry_keys.py`: a dropped non-format name is not a finding; a dropped vocabulary format still is.
- [x] 3. Proven red-first: the new non-format test fails on `origin/main`'s `registry_keys.py` and passes here.
- [x] 4. Measured on the real store: `make check-registry-keys` after `make sync-registry` reports `OK: additive only — nothing lost (112 models, 82 note(s))`; A/B on the same file, `origin/main`'s guard reports 10 LOSS findings.
- [x] 5. `agent-wiki/2026-10-27-registry-keys-format-vocab.md` + a `CHANGES.md` row name #698 and the PR; `make check-docs`, `make lint`, `make check-wiring` ok.
- [x] 6. `make test-unit` green (`5242 passed, 6 deselected`, 791.48s) and `make openspec-validate NAME=registry-keys-format-vocab` exits 0.
