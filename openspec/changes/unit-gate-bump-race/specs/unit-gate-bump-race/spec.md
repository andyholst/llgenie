# unit-gate-bump-race

## ADDED Requirements

### Requirement: the unit gate checks the registry only for tags this change did not create

`tests/test_ci_publish_order.py` MUST assert that every image `make install` pulls is published on
the real registry only for engines whose committed params are unchanged against `origin/main`. An
engine whose `containers/engines/params/<id>.json` differs from `origin/main`, or that has no copy
there, MUST be excluded and named in the test's output: its tag is built and published by the same
run's `engine-image-*` job, and waited for by `make ci-wait-engine-images` (a prerequisite of
`ci-install`, #169), never by a hermetic unit gate. The case MUST NOT be skipped or deleted, and on
`main` — where no params differ — it MUST still check every engine.

WHEN a change moves an engine pin and `make test-unit` runs
THEN the registry assertion does not require the not-yet-published tag of that engine, and it names
the engine it deferred.

#### Scenario: a bump PR defers its own new tag and checks the rest

- **Given** a checkout whose `containers/engines/params/llama.cpp.json` differs from `origin/main`
  and a registry where every other engine's cpu tag answers
- **When** the real-registry case runs
- **Then** it passes, and its output names `llama.cpp` as deferred to `ci-wait-engine-images`
- **Test:** `tests/test_ci_publish_order.py::test_a_bump_defers_its_own_new_tag_and_checks_the_rest`

#### Scenario: an engine whose params match the base is still checked

- **Given** a params file whose content is identical to its `origin/main` copy
- **When** the deferred set is computed
- **Then** that engine is not in it, so the registry assertion still covers it
- **Test:** `tests/test_ci_publish_order.py::test_a_params_file_identical_to_the_base_is_not_deferred`

#### Scenario: a param file with no base copy is deferred, never silently checked

- **Given** an engine whose params file does not exist on `origin/main`
- **When** the deferred set is computed
- **Then** that engine is in it, because the run is publishing its first tag
- **Test:** `tests/test_ci_publish_order.py::test_an_engine_with_no_base_copy_is_deferred`
