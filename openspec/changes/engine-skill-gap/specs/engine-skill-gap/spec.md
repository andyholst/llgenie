# engine-skill-gap

## ADDED Requirements

### Requirement: every registry engine is either shipped or a dated decision

`data/unsupported-engines.json` MUST record, per registry engine llgenie ships no
`skills/engines/<id>/SKILL.md` for, a `decision` (`not-shipped` or `deferred`), a
`decided` date and a `reason`. An engine in `data/models.json` with no skill and
no entry in that file MUST be reported as **new and unresolved**, never tolerated
silently, and its name MUST appear in every error.

WHEN the registry names an engine with no skill
THEN it is tolerated only as a dated decision, and an engine with no decision is
an error that names it.

#### Scenario: the shipped set, the decisions and the gap add up

- **Given** the vendored `data/models.json`, `skills/engines/*` and `data/unsupported-engines.json`
- **When** the gap is computed
- **Then** every registry engine has a status (`shipped` / `known-unsupported` / `unresolved`), and the unshipped engines are exactly the decided ones plus the unresolved ones
- **And** every decided entry carries a decision, a date and a reason
- **And** the committed `data/engine-skill-gap.json` equals a fresh computation
- **Test:** `tests/test_engine_skill_gap.py::test_every_registry_engine_has_a_status_and_the_rendered_gap_is_current`

#### Scenario: a new unskilled engine fails the gate and a dated decision silences it

- **Given** the vendored registry plus an engine no skill covers and no entry records
- **When** `check` runs
- **Then** it exits non-zero and names the engine as new and unresolved
- **And** `validate` with the decisions file names it as having no dated decision
- **And** once a dated decision is recorded and the artifact re-rendered, `check` exits 0, the engine is `known-unsupported`, and `validate` accepts it
- **Test:** `tests/test_engine_skill_gap.py::test_a_new_unskilled_engine_fails_the_gate_and_a_dated_decision_silences_it`

#### Scenario: a decision that outlives its usefulness is a failure

- **Given** a decision entry for an engine that ships a skill (or that the registry no longer names)
- **When** `check` runs
- **Then** it exits non-zero and names the entry as stale, so the record cannot rot
- **Test:** `tests/test_engine_skill_gap.py::test_a_decision_for_an_engine_that_ships_a_skill_is_stale`

#### Scenario: a malformed decision never validates silently

- **Given** a decision entry missing `reason`, or with an unknown `decision` value
- **When** the decisions file is loaded
- **Then** the load fails loudly, naming the entry
- **Test:** `tests/test_engine_skill_gap.py::test_a_malformed_decision_is_a_loud_failure_never_a_silent_pass`

### Requirement: no model vanishes — the models no engine can offer are enumerated

The gap MUST name every model that no engine llgenie ships an image for can
serve: `rank_engines` drops an engine with no image variant whether the engine has
no skill or the skill ships no image at all (`servable: false` / `via`, a drafter,
a browser library, or every variant of it disabled per #103). Those models can
never be offered, and the report MUST list them by id instead of letting them
disappear. Models that merely also list an unskilled engine MUST be reported
separately.

WHEN a model's registry engines all have no image
THEN it is listed as a model no engine can offer, by id, in the report, the
rendered artifact and the sync pull request.

#### Scenario: the permutation grid drops the engine and the artifact names the model

- **Given** a registry model served only by an engine with no skill, and the (arch, vram, ram) grid
- **When** `matrix()` runs for each case and the gap is computed
- **Then** no offered cell is that engine, the model is skipped with the engine named as the reason, and the gap lists the model under `models_never_offered`
- **Test:** `tests/test_engine_skill_gap.py::test_no_permutation_ever_offers_an_engine_with_no_skill_and_the_model_is_named`
- **Test:** `tests/test_pick_matrix_arch_perms.py::test_no_image_engine_is_never_offered_and_its_model_is_skipped_with_a_reason` (the existing hermetic grid, every arch x vram x ram)
- **Test:** `tests/test_pick_full_registry.py::test_pick_matrix_offers_only_engines_the_gap_says_have_an_image` (the existing live-registry grid against the committed gap)

#### Scenario: a model that also lists an unskilled engine is reported as such

- **Given** a model served by a shipped engine and an unskilled one
- **When** the gap is computed
- **Then** it is not in `models_never_offered`, and it is listed in `models_touching_unsupported` with the unskilled engine that put it there
- **Test:** `tests/test_engine_skill_gap.py::test_report_names_the_models_that_can_never_be_offered_and_the_per_engine_list`

### Requirement: a new unskilled engine becomes a visible work item

`spawn` MUST open exactly one issue per unresolved engine, titled for that
engine, whose body carries the evidence a reviewer needs (registry name, upstream
url, backend, the registry note, the models that list it, whether any model
depends on it alone) and the two acceptable resolutions (ship the skill, or
record the decision). It MUST be idempotent — an engine whose tracking issue is
already open MUST NOT get a second one — and a refused `gh` MUST fail the step
loudly rather than no-op.

WHEN the sync finds an engine with no skill and no decision
THEN one tracking issue exists for it, and no issue is opened for a shipped or
decided engine.

#### Scenario: one issue per unresolved engine, with the real evidence

- **Given** a registry with an unresolved engine and a `gh` that has no open issue for it
- **When** `spawn` runs
- **Then** exactly one issue is created, for that engine, and its body names the upstream url, the backend, the registry note, the models that list it and #229
- **And** no issue is created for a shipped engine
- **Test:** `tests/test_engine_skill_gap.py::test_spawn_opens_one_issue_per_unresolved_engine_with_real_evidence`

#### Scenario: spawn is idempotent and silent for a decided engine

- **Given** an engine with a dated decision
- **When** `spawn` runs
- **Then** nothing is listed and nothing is created
- **And** given an unresolved engine whose tracking issue is already open, `spawn` reports the existing issue and creates no duplicate
- **Test:** `tests/test_engine_skill_gap.py::test_spawn_is_idempotent_and_creates_nothing_for_a_decided_engine`

#### Scenario: a refused create fails the step

- **Given** an unresolved engine and a `gh` whose `issue create` exits non-zero
- **When** `spawn` runs
- **Then** the command exits non-zero and names the failed call
- **Test:** `tests/test_engine_skill_gap.py::test_spawn_fails_loudly_when_github_refuses`

### Requirement: the per-engine list is generated, committed and checked

`data/engine-skill-gap.json` MUST carry, per engine, its status, its image
variants (when it ships), the models that list it and the models it is the
top-ranked engine for, per architecture — the inverse of the trend matrix. It MUST
be generated by `make render-engine-skill-gap` and MUST be committed by the same
`registry-sync` run that rewrites the trend list; `make check-engine-skill-gap`
MUST fail when it is stale.

WHEN the trending list is synced
THEN the per-engine list and the unskilled-engine gap are regenerated in the same
run and committed with the registry.

#### Scenario: the sync regenerates the engine view with the trend list

- **Given** `.github/workflows/registry-sync.yml`
- **When** its steps and committed paths are read
- **Then** it runs `make render-engine-skill-gap` next to `make render-trend-list-matrix`, commits `data/engine-skill-gap.json`, reports the gap with `make engine-skill-gap`, and spawns a tracking issue per new engine with `secrets.BUMP_TOKEN`
- **And** it does not run the strict gate in the job, so the sync still carries the data (#219): the gate runs in `ci-unit`
- **And** the pull-request body carries the gap markdown
- **Test:** `tests/test_engine_skill_gap.py::test_the_weekly_sync_regenerates_the_gap_and_spawns_a_tracking_issue`

#### Scenario: the new test file runs in a gate

- **Given** the Makefile's `test-unit` target
- **When** it is read
- **Then** `tests/test_engine_skill_gap.py` is in it, and `make check-engine-skill-gap` is in `ci-unit`
- **Test:** `tests/test_engine_skill_gap.py::test_the_gap_test_file_runs_in_the_unit_gate`

#### Scenario: one path — the decisions file, not a loose global flag

- **Given** the Makefile and the validator CLI
- **When** the `skills-validate` recipe is read
- **Then** it passes `--unsupported <file>` when asked, `ALLOW_UNSKILLED` is gone from the tree, and `ci-unit` validates `data/models.json` against `data/unsupported-engines.json`
- **Test:** `tests/test_engine_skill_gap.py::test_skills_validate_uses_the_decisions_file_instead_of_a_global_flag`
