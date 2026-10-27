# registry-sync-gate

## ADDED Requirements

### Requirement: The generated table plans only downloads the pick can resolve

The HF class table SHALL record a `safetensors` plan only from a repo whose name does not mark
MLX, an `mlx-safetensors` plan only from a repo whose name does, and an own-checkpoint engine's
plan only for the model that engine actually serves — the same rule `plan_download()` applies
when it resolves a download. A gated Hub repository (HTTP 401/403) SHALL be reported as an
existing file that this credential may not read, never as a missing one.

WHEN the generator derives a cell for a (model, engine) pair
THEN the plan's repo matches the format the engine reads, and an own-checkpoint engine gets a plan
only for its own family.

#### Scenario: a safetensors cell is never planned from an MLX-converted repo

Given a store row whose only format repo is an MLX conversion
When  the generator derives the repos each format may be planned from
Then  `safetensors` yields none of them and `mlx-safetensors` yields all of them.

- **Test:** `tests/test_trending_quant_catalog.py::test_a_safetensors_cell_is_planned_only_from_a_non_mlx_repo`

#### Scenario: an own-checkpoint engine gets a cell only for the model it serves

Given a model Strata was measured on but does not serve
When  its catalog cell is generated
Then  no Strata cell is invented, and the same model served by Strata does get its own plan.

- **Test:** `tests/test_trending_quant_catalog.py::test_a_strata_cell_exists_only_for_the_family_strata_serves`

#### Scenario: a gated link verifies and says it is gated

Given a Hub repository that answers 401 to an unauthenticated ranged GET
When  the shared live probe checks one of its files
Then  the link counts as existing, is marked gated, and is not retried.

- **Test:** `tests/test_hub_probe.py::test_a_gated_file_verifies_and_says_it_is_gated`

### Requirement: An engine is offered only when a plan for it can be downloaded

For a model the committed table covers, `rank_engines` SHALL NOT offer an engine that has no cell
for that model. A model the table does not cover yet SHALL keep the previous behaviour (live
resolution), so a store synced a step before its catalog is still served.

WHEN the pick ranks the engines a model was measured on
THEN every engine it keeps is one the table can plan a download for — or the model is not in the
table at all.

#### Scenario: an engine with no cell is not offered for a covered model

Given a model the table covers with llama.cpp only, measured on MLX as well
When  the engines are ranked for a CUDA host
Then  only llama.cpp is offered.

- **Test:** `tests/test_model_engine_pick.py::test_an_engine_with_no_catalog_cell_is_not_offered_for_a_covered_model`

#### Scenario: a model the table does not cover keeps its engines

Given a table rendered for other models
When  a measured model it does not mention is ranked
Then  every engine it was measured on is still offered.

- **Test:** `tests/test_model_engine_pick.py::test_a_model_the_catalog_does_not_cover_keeps_its_engines`

#### Scenario: every engine the pick offers on the synced store is catalogued

Given the vendored store and its committed table
When  every row plain `llgenie` offers is read
Then  each offered engine has a cell listing the arch it is offered on, and every row that serves
nothing carries a reason.

- **Test:** `tests/test_trending_quant_catalog.py::test_every_engine_and_arch_that_llgenie_offers_is_catalogued`

### Requirement: The rendered trend list is the list matrix() considered

The committed per-(arch, vram, ram) list SHALL be built from the same model set `matrix()` used,
including the store's `system_ram_min` floor, so a printed row is never both server-less and
reason-less. Growing the system RAM SHALL only add rows.

WHEN the trend-list matrix is rendered for a (arch, vram, ram) case
THEN its rows are the models `matrix()` gated in, and every row is either served or explained.

#### Scenario: a row a RAM floor excludes is not printed blank

Given the committed CUDA 16 GB lists at 8 GB and at 64 GB of RAM
When  the rows are compared
Then  more RAM only adds served rows, and every listed row is served or says why.

- **Test:** `tests/test_trend_list_matrix.py::test_ram_changes_which_cuda_16gb_model_is_served`

#### Scenario: the committed list matches matrix() for every case

Given the committed `tests/fixtures/trend-list-matrix.json`
When  `matrix()` runs for each (arch, vram, ram) case
Then  the rows are identical, in README order.

- **Test:** `tests/test_trend_list_matrix.py::test_trend_list_matches_the_committed_matrix`

### Requirement: A hermetic pick test resolves its own stubs

A test file that stubs the Hub and the engine registry SHALL also disable the committed HF class
table, so a stub model id that upstream happens to list is answered by the stub.

WHEN a stubbed pick test runs
THEN no cell of the committed table takes part in its answer.

#### Scenario: a stub id that upstream also lists is answered by the stub

Given the stubbed Hub, engine registry and a catalog disabled
When  the exhaustive permutation grid is computed
Then  every runnable cell resolves through the stub trees and `use_format` stays `gguf`.

- **Test:** `tests/test_pick_matrix_arch_perms.py::test_exhaustive_perms_all_map_to_fitting_hf_urls`

### Requirement: Every engine the store names is shipped or decided

Each engine the vendored store lists SHALL have a skill or a dated, reasoned entry in
`data/unsupported-engines.json` naming the upstream it was read from. A store that names an
undecided engine SHALL fail `make check-engine-skill-gap`.

WHEN the weekly sync derives the gap for a store that names a new engine
THEN the gate fails naming that engine until a skill ships or a dated decision exists.

#### Scenario: a new unskilled engine fails the gate, a dated decision silences it

Given a store naming an engine with no skill and no decision
When  `engine_skill_gap check` runs
Then  it fails naming the engine, and the same store passes once the decision is recorded.

- **Test:** `tests/test_engine_skill_gap.py::test_a_new_unskilled_engine_fails_the_gate_and_a_dated_decision_silences_it`

#### Scenario: the real store's 42 engines are all resolved

Given the synced store and the committed decisions
When  the gap is checked
Then  zero engines are unresolved and the rendered gap is current.

- **Test:** `tests/test_engine_skill_gap.py::test_the_real_files_are_current_and_the_gate_agrees_with_the_gap`
