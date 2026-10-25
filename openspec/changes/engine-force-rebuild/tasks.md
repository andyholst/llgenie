# Tasks

- [ ] 1. `openspec/changes/engine-force-rebuild` — proposal + `specs/engine-force-rebuild/spec.md` (G/W/T, a `- **Test:**` line per scenario) + this checklist, written before the code (issue #638)
- [ ] 2. `scripts/engine_image.py` — `_buildx(force=)`: `--no-cache` and no `--cache-from` when forced; `build_base(force=)` and `build(force=)` pass it through; `build()` passes `force` to `build_base()`
- [ ] 3. `Makefile` — `build-engines` forwards `FORCE=1` into every row's `make build-engine`; `##` help lines for `build-engine` and `build-engines` document the flag
- [ ] 4. `.github/workflows/engine-build.yml` — `force` dispatch input (default `false`) wired to `FORCE=1` on the build step only; header `Trigger surface` / `Flow` / `Never` updated
- [ ] 5. `tests/test_engine_force_rebuild.py` — forced vs unforced `buildx` argv, `force` reaching `build_base()`, `build-engines` forwarding `FORCE`
- [ ] 6. `tests/test_engine_build_workflow.py` — the `force` input exists, defaults to `false`, is wired to the build step only, and the build → verify → push order still holds
- [ ] 7. `README.md` — `FORCE=1` on `build-engine` / `build-engines` and in the workflow's input list (with `push` = republish)
- [ ] 8. `agent-wiki/2026-10-25-engine-force-rebuild.md` — the work record, referencing issue #638 and its PR
- [ ] 9. Verified: `make openspec-validate NAME=engine-force-rebuild`, `make check-workflows`, `make check-dispatch-forms`, `make check-docs`, `make check-wiring`, `make lint`, plus the two test files in the test image and a real `make build-engine ENGINE=llama.cpp ARCH=cpu FORCE=1`
