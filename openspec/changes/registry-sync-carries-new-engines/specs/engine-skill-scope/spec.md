# engine-skill-scope

## ADDED Requirements

### Requirement: a data-carrying job tolerates a NEW engine, ci-unit does not

`scripts/engine_skills.py validate` MUST accept `allow_new_engines` (`--allow-new-engines`, Makefile
`ALLOW_NEW_ENGINES=1`). With the flag, a registry engine that has no skill and no dated decision in
`data/unsupported-engines.json` is **named and tolerated** — it is a new upstream engine whose
tracking issue this run opens. Without it, that engine MUST be an error naming it as new and
unresolved. The flag MUST NOT hide a skill whose engine is gone from the registry, and it MUST NOT be
passed from `ci-unit`.

WHEN the weekly registry sync meets a store that first names an engine llgenie does not ship
THEN the store is carried, the engine is named, and its tracking issue is opened.

#### Scenario: the strict scope refuses a new engine and the carrying scope names it

- **Given** the real skills and a registry listing every engine they ship plus one new engine with no decision
- **When** the validator runs with and without `allow_new_engines`
- **Then** the strict run returns exactly the new-and-unresolved error for that engine
- **And** the carrying run returns no errors
- **Test:** `tests/test_registry_sync_trend.py::test_a_new_engine_is_carried_with_the_flag_and_refused_without_it`

#### Scenario: the job's check step carries, ci-unit stays strict

- **Given** `.github/workflows/registry-sync.yml` and the `ci-unit` target
- **When** their `skills-validate` invocations are read
- **Then** the sync's step pins `REGISTRY=data/models.json`, `UNSUPPORTED=data/unsupported-engines.json` **and** `ALLOW_NEW_ENGINES=1`
- **And** no `ci-unit` line passes `ALLOW_NEW_ENGINES`
- **Test:** `tests/test_registry_sync_trend.py::test_the_sync_job_validates_the_registry_it_just_synced`

#### Scenario: a skill whose engine left the registry still fails in the carrying scope

- **Given** a registry missing the engine one shipping skill declares
- **When** the validator runs with `allow_new_engines=True`
- **Then** it still reports that engine is not a key in the registry
- **Test:** `tests/test_registry_sync_trend.py::test_a_new_engine_is_carried_with_the_flag_and_refused_without_it`

### Requirement: the sync job opens the tracking issue it tolerates

The step after the check MUST run `make spawn-engine-skill-issues` for the carried engines, and the
sync's own gate MUST stay the report form (`make engine-skill-gap`), never `make check-engine-skill-gap`
— that gate belongs to `ci-unit`, which refuses the resulting PR until the engine ships or is decided.

WHEN the sync carries a new engine
THEN one tracking issue exists per new engine and the PR is red in ci-unit until it is decided.

#### Scenario: the sync spawns the issue and does not run the ci-unit gate

- **Given** the registry-sync workflow
- **When** its steps are read
- **Then** it spawns one issue per unresolved engine with the sync token
- **And** its check step does not run `make check-engine-skill-gap`
- **Test:** `tests/test_engine_skill_gap.py::test_the_weekly_sync_regenerates_the_gap_and_spawns_a_tracking_issue`
