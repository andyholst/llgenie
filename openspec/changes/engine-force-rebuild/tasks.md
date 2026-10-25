# Tasks

- [x] 1. `openspec/changes/engine-force-rebuild` — proposal + `specs/engine-force-rebuild/spec.md` (G/W/T, a `- **Test:**` line per scenario) + this checklist, written before the code (issue #638)
- [x] 2. `scripts/engine_image.py` — `_buildx(force=)`: `--no-cache` and no `--cache-from` when forced; `build_base(force=)` and `build(force=)` pass it through; `build()` passes `force` to `build_base()`
- [x] 3. `Makefile` — `build-engines` forwards `FORCE=1` into every row's `make build-engine`; `##` help lines for `build-engine` and `build-engines` document the flag
- [x] 4. `.github/workflows/engine-build.yml` — `force` dispatch input (default `false`) wired to `FORCE=1` on the build step only; header `Trigger surface` / `Flow` / `Never` updated
- [x] 5. `tests/test_engine_force_rebuild.py` — forced vs unforced `buildx` argv, `force` reaching `build_base()`, `build-engines` forwarding `FORCE`
- [x] 6. `tests/test_engine_build_workflow.py` — the `force` input exists, defaults to `false`, is wired to the build step only, and the build → verify → push order still holds
- [x] 7. `README.md` — `FORCE=1` on `build-engine` / `build-engines` and in the workflow's input list (with `push` = republish)
- [x] 8. `agent-wiki/2026-10-25-engine-force-rebuild.md` — the work record, referencing issue #638 and its PR
- [x] 9. Verified: `make openspec-validate NAME=engine-force-rebuild`, `make check-workflows`, `make check-dispatch-forms`, `make check-docs`, `make check-wiring`, `make lint`, plus the test files in the test image and a real forced build: `make build-engine ENGINE=llama.cpp ARCH=cpu FORCE=1` → `buildx … --no-cache` for the base and the engine, 396 compiler lines, no `--cache-from`, then `make test-engine-image ENGINE=llama.cpp ARCH=cpu` → 3 passed
