# 2026-10-25 — FORCE=1 really rebuilds, and a publish carries hash + arch + latest

Issue: [#638](https://github.com/asimov-agent/llgenie/issues/638)
OpenSpec: `openspec/changes/engine-force-rebuild`
Complements: [#614](https://github.com/asimov-agent/llgenie/issues/614) (the sweep itself)

## What changed

The dispatched sweep could only ever validate what the layer cache already held: every row printed
`… available -> no rebuild`, and `make build-engine FORCE=1` did not help, because `build(force=True)`
skipped the availability check and then called `_buildx()` unchanged — which still passed
`--cache-from type=registry,…:buildcache-<variant>`, so a fully cached build re-tagged the previous
layers instead of compiling. Two gaps made a forced sweep impossible at all: `make build-engines`
forwarded `PUSH` and `VERIFY` into each row but not `FORCE`, and `build()` called
`build_base(spec["backend"], push=push)` **without** `force`, so the shared toolchain base was never
rebuilt.

- `scripts/engine_image.py`: `_buildx()` takes `force` and, when set, passes `--no-cache` and **no**
  `--cache-from` (the registry cache is not read; the fresh layers are still written back for later
  runs). `build_base()` and `build()` carry `force` through, and `build()` now calls
  `build_base(…, force=force, …)`.
- `Makefile`: `build-engines` forwards `FORCE=1` into every row next to `PUSH`/`VERIFY`; the `##`
  help lines of `build-engine` and `build-engines` state what `FORCE` does.
- `.github/workflows/engine-build.yml`: new `force` dispatch input (default `false`), wired as
  `FORCE` on the build step only — verification and publishing keep their order and their guards.

## Publishing names (same issue)

`push()` now publishes every image through `publish_refs()`: the immutable **hash tag**
(`<sha8>-<hash>-<variant>`), the moving **`:<arch>`** tag, and **`:latest`** — and `:latest` is claimed
by exactly one variant per engine (`cpu` when the engine has one, else its only/first variant), so
parallel rows cannot race to point it at another backend. `pull_published()` checks the digest of
every one of those refs against the hash tag, so a `:latest` that drifted fails the published-image
test instead of passing.

## Verified

- `tests/test_engine_force_rebuild.py` (9 cases): `--no-cache` present when forced and absent
  otherwise, `--cache-from` dropped when forced (local and pushing builds), an available image no
  longer short-circuits a forced build, `build_base()` receives `force=True`, `build-engines`
  forwards `FORCE`, the three publish refs (cpu vs cuda), a gpu-only engine still getting `:latest`,
  and exactly one `:latest` owner per engine across the committed params.
- `tests/test_engine_build_workflow.py`: the `force` input exists, defaults to `false`, is wired to
  the build step and never to the push step.
- `tests/test_engine_skills.py`: the push expectations now assert all three refs.
- Gates: `make openspec-validate NAME=engine-force-rebuild`, `make check-workflows`,
  `make check-dispatch-forms`, `make check-docs` (198 targets), `make check-wiring`, `make lint`.
- Real forced build: `make build-engine ENGINE=llama.cpp ARCH=cpu FORCE=1` recompiles the cell with
  `--no-cache` (the build log carries the flag) and the image still passes `make test-engine-image`.

## Status

Implemented and tested; the PR references #638. The remaining engine-side work is unchanged and
tracked elsewhere: prebuilt/wheel cells (#615) and the four `DISABLED` cells (#103).
