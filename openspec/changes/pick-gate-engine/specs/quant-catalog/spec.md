# quant-catalog spec delta

## ADDED Requirements

### Requirement: The catalog check fails on a lost plan, and notes what the live Hub re-reads

`make check-quant-catalog` SHALL fail when a row the committed
`data/trending-quant-catalog.json` HAS is no longer produced by
`scripts/gen_trending_quant_catalog.py` — a plan gone, a plan whose repo/files/size/link
changed, an engine's arch list changed, or a table rendered for another registry.

It SHALL NOT fail on what the live Hub re-reads: `mlx_repos()`/`tensorfold_repos()` query a
`sort=downloads` search, so the same plans come back in a different order as those counts
move, and a conversion upstream publishes shows up as an extra row. Both SHALL be printed as
a `[quant-catalog] NOTE:` line and the check SHALL exit 0, because recording them is the
weekly `make sync-quant-catalog`'s job.

WHEN the committed table still regenerates to the same set of plans in a different order,
THEN the check exits 0 and names the reordered (model, engine) cell in a note.

WHEN the generator no longer produces a plan the committed table records,
THEN the check exits 1 and names that plan's URL.

#### Scenario: a plan the committed table lost still fails

Given a committed table whose cell records a plan,
When the generator regenerates that cell without it,
Then the check fails, naming the plan it can no longer produce.
- **Test:** `tests/test_trending_quant_catalog.py::test_a_plan_the_committed_table_has_and_the_generator_lost_still_fails`

#### Scenario: a changed plan still fails

Given a committed plan pointing at one file,
When the generator regenerates it pointing at another,
Then the check fails, because the committed table would ship an unverified download.
- **Test:** `tests/test_trending_quant_catalog.py::test_a_changed_plan_still_fails`

#### Scenario: a reorder is reported, never failed

Given a committed cell whose plans the live search now returns in a different order,
When the check compares the committed table with a fresh generation,
Then the reorder is a note and the exit status stays 0.
- **Test:** `tests/test_trending_quant_catalog.py::test_a_reordered_regeneration_is_a_note_not_a_failure`

#### Scenario: a conversion upstream published is reported, never failed

Given a fresh generation holding a plan the committed table does not record yet,
When the check compares the two,
Then the addition is a note and the exit status stays 0.
- **Test:** `tests/test_trending_quant_catalog.py::test_a_repo_upstream_publishes_since_the_sync_is_a_note_not_a_failure`

#### Scenario: a table rendered for another registry fails

Given a committed table rendered for an older `data/models.json`,
When the vendored store states a newer `generated_utc`,
Then the check fails and says to run `make sync-quant-catalog`.
- **Test:** `tests/test_trending_quant_catalog.py::test_a_catalog_rendered_for_another_registry_still_fails`
