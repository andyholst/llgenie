# weekly-registry-sync — modified by engine-skill-gap

## MODIFIED Requirements

### Requirement: the trending registry syncs weekly without failing on an engine llgenie does not ship

`registry-sync` MUST run on cron `17 5 * * 1` and on `workflow_dispatch`. That
cron MUST stay distinct from `engine-bump` (`23 6 * * 1`). The job MUST
byte-copy upstream `data/models.json` and `README.md` into `data/models.json` and
`data/trending-README.md`, regenerate `data/trending-quant-catalog.json`,
`tests/fixtures/trending-quant-catalog.json`, `tests/fixtures/trend-list-matrix.json`
**and `data/engine-skill-gap.json`**, and open or update `chore/registry-sync`
with `secrets.BUMP_TOKEN` when those files differ from `main`. The job MUST NOT
merge and MUST NOT change `skills/engines/**`.

`engine_skills.validate` MUST still report a registry engine that has no skill.
Tolerating one MUST be a **dated decision** in `data/unsupported-engines.json`
(issue #229): `make skills-validate REGISTRY=data/models.json
UNSUPPORTED=data/unsupported-engines.json` and `make check-engine-skill-gap`
MUST tolerate the decided engines and MUST report a registry engine with no skill
and no decision as new and unresolved, naming it. A skill whose `engine:` is not a
registry key MUST still be an error. The default `make skills-validate` against
`tests/fixtures/trending-models.json` MUST stay strict. The global
`ALLOW_UNSKILLED=1` flag MUST be gone.

WHEN the weekly job finds a newer upstream registry
THEN it opens one pull request with the regenerated trend list and per-engine gap,
reports the engines llgenie does not ship, opens one tracking issue per NEW
unskilled engine, and does not fail the job on them — the strict gate is
`ci-unit` on the pull request.

#### Scenario: the workflow is weekly, accounts for unshipped engines, and opens a pull request with the owner token

- **Given** `.github/workflows/registry-sync.yml`
- **When** its schedule, its validate/step list, and its pull-request step are read
- **Then** the cron is `17 5 * * 1`, the job reports the gap with `make engine-skill-gap` and spawns a tracking issue per new engine, and the pull request uses `secrets.BUMP_TOKEN`
- **And** the committed paths are `data/models.json`, `data/trending-README.md`, `data/trending-quant-catalog.json`, `tests/fixtures/trending-quant-catalog.json`, `tests/fixtures/trend-list-matrix.json`, and `data/engine-skill-gap.json`
- **And** the job rewrites the trend-list matrix with `make render-trend-list-matrix` and the per-engine gap with `make render-engine-skill-gap` before it commits
- **And** `ALLOW_UNSKILLED` is absent from the workflow, and the workflow does not merge and does not add a file under `skills/`
- **Test:** `tests/test_registry_sync_trend.py::test_registry_sync_workflow_is_weekly_and_accounts_for_unskilled_engines`
- **Test:** `tests/test_engine_skill_gap.py::test_the_weekly_sync_regenerates_the_gap_and_spawns_a_tracking_issue`

#### Scenario: an engine with no skill fails a strict validate and a decided one is tolerated

- **Given** the 2026-10-05 registry fixture plus an engine no skill covers
- **When** `validate` runs with and without the decisions file
- **Then** the strict run names that engine as having no skill, the decided run tolerates it only because `data/unsupported-engines.json` records it, and an engine with no decision is named as new and unresolved
- **And** removing a skill's engine from the registry is still an error
- **Test:** `tests/test_registry_sync_trend.py::test_a_dated_decision_omits_an_unknown_engine_and_dropping_ours_is_still_an_error`

#### Scenario: the live registry's undecided engines are reported, never loosened

- **Given** the live upstream registry downloaded by `sync_registry.sync`
- **When** it is validated with the decisions file
- **Then** the only errors are the engines upstream lists with no skill and no decision, each named, and the strict run names every unskilled engine
- **Test:** `tests/test_registry_sync_trend.py::test_live_sync_adopts_a_higher_skilled_tps_for_models_that_fit_48gb`
