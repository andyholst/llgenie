# pick-gate spec delta

## MODIFIED Requirements

### Requirement: A model fits by its measured minimum

The picker SHALL decide whether a model fits this host from the store's own statement, in
this order: `vram_min` when the store states one, else `vram_tier`. When the store states
`system_ram_min`, the host's RAM SHALL also be at least that.

WHEN a host's card is 16 GB and the store states `vram_min` 12 GB, `vram_tier` 16 GB,
THEN the model is offered.

WHEN a host's card is 16 GB and the store states `vram_min` 32 GB,
THEN the model is not offered, whatever `vram_tier` says.

WHEN the store states no `vram_min` for a model,
THEN `vram_tier` is the gate, exactly as before.

#### Scenario: the measured minimum is the gate
Given a model whose `vram_min` and `vram_tier` disagree,
When `fits(model, 16)` runs for a 16 GB card,
Then it answers from `vram_min`, never from the tier — in both directions.
- **Test:** `tests/test_registry_footprint.py::test_the_gate_reads_the_stated_minimum_not_the_display_tier`

#### Scenario: the system-RAM floor is applied when the store states one
Given a model that states `system_ram_min` above this host's RAM,
When `fits()` is asked whether it fits,
Then it answers no, even when the card is big enough.
- **Test:** `tests/test_trend_pick.py::test_card_16gb_list_on_this_readme`

#### Scenario: the printed trend list applies the same floors
Given plain `llgenie --trend` on a host with a card and known RAM,
When it prints the numbered list,
Then every listed model fits by `fits()` and no model that does not fit is numbered.
- **Test:** `tests/test_trend_pick.py::test_llgenie_list_is_the_readme_list_that_fits_the_card`

#### Scenario: the matrix applies the same floors as the pick
Given `llgenie --matrix` with no `--ram` on a host whose RAM is known,
When it builds the permutation map,
Then the host's RAM is resolved the way the card is, so a model above the store's
`system_ram_min` is not listed — the matrix never offers what `offer()` refuses.
- **Test:** `tests/test_pick_full_registry.py::test_pick_matrix_any_offer_is_a_real_fitting_hf_url`

#### Scenario: a format written in another spelling is still that format
Given a `formats[].name` of `LiteRT-LM`,
When the normaliser maps it to the vocabulary,
Then it is `litertlm` and the entry survives, never restated as GGUF.
- **Test:** `tests/test_trend_pick.py::test_plan_download_per_format_live_hub`

## ADDED Requirements

### Requirement: The suite asserts rules over the store, not rows in it

Tests SHALL derive what they assert from the vendored store and from `offer()`: no model
name, engine name, t/s figure, row index or README order SHALL be pinned.

WHEN upstream adds, removes, renames or re-measures a row,
THEN the suite keeps passing without an edit, and fails only when a rule is broken.

#### Scenario: the fitting set is the product's own decision
Given a card size and the vendored store,
When a test needs the models that fit,
Then it reads them from `mp.fits()` in the store's order, not from the README's VRAM cell.
- **Test:** `tests/test_trend_list_acceptance.py::test_225_acceptance_strata_on_a_16gb_card`

#### Scenario: the README's column is a stated figure, whichever one it prints

Given the vendored store and the README it was synced with,
When a test compares a row's README VRAM cell with the store,
Then the cell matches a figure the store states for that model — the measured minimum, else
the display tier — because WHICH of the two upstream prints moves with a sync (the
2026-10-13 store prints the tier, the 2026-10-27 one the measured minimum), and the suite
never freezes either.
- **Test:** `tests/test_trend_list_acceptance.py::test_the_vendored_store_states_two_distinct_vram_figures`,
  `tests/test_trend_pick.py::test_vendored_registry_is_the_vendored_readme_list`

#### Scenario: the TensorFold seams follow the row the store serves
Given a 48 GB Mac and a store whose top row is served by another engine,
When a TensorFold test picks,
Then it picks the row the store lets TensorFold serve, at that row's printed position.
- **Test:** `tests/test_tensorfold_seamless.py::test_select_shows_what_picking_tensorfold_will_do`

#### Scenario: a renamed engine in a copy is rejected
Given the README copied with one model's best CUDA engine renamed,
When the sync checks it against the store,
Then it fails naming the engine, because the store does not list it.
- **Test:** `tests/test_trend_pick.py::test_readme_copy_passes_and_a_modified_copy_is_rejected`
