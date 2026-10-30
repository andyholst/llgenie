# Tasks — check-docs-fragment-only-agrees

- [x] 1. Prove the disagreement at `main@6d118a03`: plant a note + its `docs/changes.d/` fragment, leave `CHANGES.md` untouched, show `make check-docs` exit 0 and `tests/test_check_docs.py::test_the_real_tree_documents_every_user_facing_target` + `tests/test_changes_index.py::test_the_real_index_renders_the_committed_changes_md` failing.
- [x] 2. `tests/test_check_docs.py`: the real-tree test asserts membership (`CHANGES.md` links no note that does not exist, a stale index may lag) instead of exact equality with the note set.
- [x] 3. `tests/test_check_docs.py`: new behaviour test — a fragment-only change is green through `check_docs.problems()` and through `scripts/check_docs.py check`, and a committed row linking a missing note is red in both.
- [x] 4. `tests/test_changes_index.py`: the real-tree test accepts `committed == rendered` or a reported lag and asserts every committed row is one the renderer writes.
- [x] 5. `tests/test_changes_index.py`: `write` determinism and idempotence move onto a scratch tree, so no test edits the real `CHANGES.md`.
- [x] 6. `openspec/changes/changes-index-per-change-file/specs/documentation-surface/spec.md`: restate the landed "committed table is the renderer's output" scenario to the lagging-index contract and update its test reference.
- [x] 7. `docs/ARCHITECTURE.md`: the gate's description states the lagging-index rule.
- [x] 8. Sabotage loop: reintroduce the fragment-only shape (note + fragment, no `CHANGES.md` edit), show the two tests red before the fix and green after, restore.
- [x] 9. `agent-wiki/2026-10-30-check-docs-fragment-only-agrees.md` + its `docs/changes.d/` fragment state the contract and name #1100 / the PR.
- [x] 10. `make check-docs`, the two touched test modules and `make test-unit` green; `make openspec-validate NAME=check-docs-fragment-only-agrees` exits 0.
