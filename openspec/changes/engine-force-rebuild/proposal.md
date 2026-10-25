# engine-force-rebuild — proposal

Issue: [#638](https://github.com/asimov-agent/llgenie/issues/638)

## Why

The dispatched sweep builds and verifies every cell (`engine-build.yml`, run 40219845000: 29 jobs,
all green), but it can only ever work with what the layer cache already holds. Every row reports
`… available -> no rebuild`, and `make build-engine FORCE=1` does not change that: `build(force=True)`
skips the local/registry availability check and then calls `_buildx()` unchanged, which still passes
`--cache-from type=registry,ref=…buildcache-<variant>` — a fully cached build re-tags the previous
layers instead of recompiling. Two more gaps make a forced sweep impossible at all:
`make build-engines` forwards `PUSH` and `VERIFY` into each row but **not** `FORCE`, and
`build()` calls `build_base(spec["backend"], push=push)` **without** `force`, so the shared toolchain
base is never rebuilt.

So after a base/toolchain change, a poisoned cache, or a GHCR tag that must come from a clean build,
there is no way to say "rebuild all of it and republish".

## What Changes

- **`scripts/engine_image.py`** — `_buildx()` takes `force` and, when set, adds `--no-cache` and
  drops `--cache-from` (the build genuinely recompiles). `build_base()` and `build()` take `force`
  through to it, and `build()` passes `force` to `build_base()`, so the shared base is rebuilt too.
- **`Makefile`** — `build-engines` forwards `FORCE=1` into every row's `make build-engine`; the
  `##` help lines for `build-engine` and `build-engines` document the flag.
- **`.github/workflows/engine-build.yml`** — a `force` input (`workflow_dispatch`, default `false`)
  wired to `FORCE=1` on each row's build step, so a dispatched run can rebuild the whole matrix and
  (with `push=true`) republish every tag from a clean build. Verification is unchanged: build →
  probe the binary → publish.
- **`tests/test_engine_force_rebuild.py`** (new) — `--no-cache` present when forced and absent
  otherwise, `--cache-from` dropped when forced, `build()` forwarding `force` to `build_base()`, and
  `build-engines` forwarding `FORCE`.
- **`tests/test_engine_build_workflow.py`** — the `force` input exists, defaults to `false`, and is
  wired to the build step only (never to the verification or publish step).
- README documents the flag on both targets and in the workflow's input list; `agent-wiki/` records
  the change.

Not covered: scheduling the sweep (#614), re-enabling the four `DISABLED` cells (#103), converting
the remaining wheel/tarball cells to source builds (#615).
