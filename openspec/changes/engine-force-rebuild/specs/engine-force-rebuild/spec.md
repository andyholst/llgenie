# engine-force-rebuild

## ADDED Requirements

### Requirement: FORCE rebuilds instead of reusing the cache

`make build-engine … FORCE=1` MUST rebuild the image even when the tag is available locally or in the
registry, and MUST NOT read the layer cache: the build passes `--no-cache` and no `--cache-from`, so
the engine actually recompiles. Without `FORCE`, the existing behaviour is unchanged (a cached build
may be reused).

WHEN a maintainer asks for a forced build of a cell
THEN `buildx` runs with `--no-cache` and without `--cache-from`, and nothing is skipped because the
tag already exists.

#### Scenario: a forced build bypasses the cache

- **Given** a cell whose image is available locally and whose layers are in the registry cache
- **When** it is built with `FORCE=1`
- **Then** `buildx` is invoked with `--no-cache` and without `--cache-from`
- **Test:** `tests/test_engine_force_rebuild.py::test_a_forced_build_passes_no_cache_and_drops_cache_from`

#### Scenario: an unforced build keeps the cache

- **Given** the same cell
- **When** it is built without `FORCE`
- **Then** `buildx` reads the registry cache and passes no `--no-cache`
- **Test:** `tests/test_engine_force_rebuild.py::test_an_unforced_build_keeps_the_registry_cache`

### Requirement: a forced engine build rebuilds its shared base

A forced build MUST pass `force` to `build_base()`, so the shared toolchain base for that backend is
rebuilt rather than reused — otherwise a stale base silently undermines the forced engine build.

WHEN a cell is built with `FORCE=1`
THEN the shared base for its backend is built with `force=True`.

#### Scenario: the base inherits the force

- **Given** a cell built with `force=True`
- **When** its `build()` runs
- **Then** `build_base()` receives `force=True`
- **Test:** `tests/test_engine_force_rebuild.py::test_a_forced_build_forces_the_shared_base_too`

### Requirement: the whole sweep can be forced

`make build-engines FORCE=1` MUST forward `FORCE=1` into every row it fans out, alongside the
existing `PUSH` and `VERIFY`, so the whole matrix can be rebuilt in one command.

WHEN the sweep is asked for a forced rebuild
THEN every row's `make build-engine` carries `FORCE=1`.

#### Scenario: the sweep forwards the flag

- **Given** `make build-engines`'s recipe
- **When** it is read
- **Then** the per-row `make build-engine` invocation carries the `FORCE` conditional
- **Test:** `tests/test_engine_force_rebuild.py::test_build_engines_forwards_force_to_every_row`

### Requirement: the dispatch workflow can rebuild and republish

`.github/workflows/engine-build.yml` MUST expose a `force` dispatch input, defaulting to `false`, wired
to `FORCE=1` on each row's build step. Verification and publishing MUST stay unchanged: a forced row is
still built, its binary probed, and only then pushed when `push=true` (which overwrites the tag).

WHEN a maintainer dispatches with `force=true` and `push=true`
THEN every row rebuilds from a clean cache, is verified, and republishes its tag.

#### Scenario: the workflow carries the input

- **Given** `engine-build.yml`
- **When** its inputs and build step are read
- **Then** `force` defaults to `false` and the build step passes `FORCE` only when it is true
- **Test:** `tests/test_engine_build_workflow.py::test_the_dispatch_can_force_a_rebuild`

#### Scenario: a forced run still verifies before publishing

- **Given** the same workflow
- **When** the step order is read
- **Then** `make build-engine … FORCE=1` precedes `make test-engine-stage`, which precedes
  `make push-engine`
- **Test:** `tests/test_engine_build_workflow.py::test_every_row_is_built_and_then_verified`
