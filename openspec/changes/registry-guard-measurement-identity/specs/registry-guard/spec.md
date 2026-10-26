# registry-guard

## ADDED Requirements

### Requirement: A measurement is identified by its source post, store-wide

The additive-only guard MUST identify a measurement by the `/status/<id>` of its `source_post`, searched
across the WHOLE store (`engines[]` measurements and `engagement.seen_posts`), never by the exact
`(engine, hardware)` pair. A hardware string that upstream refined, a post re-attributed to a more
specific model row, a post that moved between a ranked row and the `seen_posts` placeholder, and a profile
link upgraded to its real status URL MUST NOT be reported as a loss. A value that carries no `/status/<id>`
(a profile link) MUST NOT be tracked as a post identity.

WHEN the guard compares the committed store with a sync that only rewrote bookkeeping upstream regenerates
THEN it reports no loss and exits 0.

#### Scenario: a refined hardware label is not a lost measurement

- **Given** a committed store whose measurement "llama.cpp on RTX 4070" cites a status post
- **And** a sync whose same post now says "llama.cpp on RTX 4070 12GB"
- **When** the guard compares them
- **Then** no loss is reported and the guard exits 0
- **Test:** `tests/test_registry_keys.py::test_compare_ignores_what_upstream_rewrites_in_place`

#### Scenario: a post re-attributed to a split model row is not lost

- **Given** a committed store where model `m1` carries an MLX measurement and its seen-post
- **And** a sync where that measurement now lives on a new model row `m1-mlx`
- **When** the guard compares them
- **Then** the post is not reported as gone from the store
- **Test:** `tests/test_registry_keys.py::test_a_tracked_post_is_one_identity_across_the_whole_store`

#### Scenario: a post demoted to the seen_posts placeholder is not lost

- **Given** a model with two ranked llama.cpp runs, one citing post `/status/3`
- **And** a sync where that run is now only an entry in `engagement.seen_posts`
- **When** the guard compares them
- **Then** nothing is reported as lost
- **Test:** `tests/test_registry_keys.py::test_a_post_moved_to_the_seen_posts_placeholder_is_not_lost`

#### Scenario: a post that is nowhere in the new store is a loss

- **Given** a committed store whose model cites post `/status/2`
- **And** a sync whose every model row and every placeholder dropped that post
- **When** the guard compares them
- **Then** it reports the post as gone from the store and exits 1
- **Test:** `tests/test_registry_keys.py::test_a_post_deleted_from_the_store_is_a_loss`

### Requirement: The guard fails only on what really thins the ranked set

The guard MUST exit 1 when a model row is gone, when a key is gone from a model row, when an engine that
had a measurement for the model has none, when a `backends` / `supported_engines` entry or a `formats` name
is gone, when an engine-registry entry is gone, or when a stated footprint scalar (`weight_gb`,
`context_tokens`, `system_ram_min`) is lowered — on the model or on a measurement of a surviving post. It
MUST NOT fail on a lowered t/s, a decreased engagement counter or a shrunken `seen_posts` placeholder for a
surviving post; those are printed as notes with both numbers.

WHEN a sync loses a model, key, engine, list entry, engine-registry entry or stated footprint
THEN the guard names it and exits 1, whether or not any figure moved.

#### Scenario: every real loss is still reported

- **Given** a committed store and a sync that drops a model, a model key, an engine's last measurement, a
  backend, a supported engine, a format, an engine-registry entry, or lowers a stated footprint
- **When** the guard compares them
- **Then** each one is reported with the model or field named
- **Test:** `tests/test_registry_keys.py::test_compare_reports_every_kind_of_loss`

#### Scenario: a lowered counter or re-stated t/s is a note, never a failure

- **Given** a committed store and a sync that lowers an engagement counter, re-states a post's t/s lower
  and empties a `seen_posts` placeholder
- **When** the guard runs on the command line
- **Then** it exits 0 and prints each movement as a `NOTE:` with both numbers, and no `LOSS`
- **Test:** `tests/test_registry_keys.py::test_cli_fails_a_lossy_sync_and_passes_an_additive_one`

#### Scenario: a lowered footprint of a surviving run is still a loss

- **Given** a committed store whose measurement states `weight_gb: 10GB Q4_K_M` for a post
- **And** a sync that states `4GB Q4_K_M` for the same post
- **When** the guard compares them
- **Then** it reports the lowered footprint and exits 1
- **Test:** `tests/test_registry_keys.py::test_compare_reports_every_kind_of_loss`

### Requirement: A clean tree and the live store both pass

The guard MUST report no loss when the committed store is compared with itself, and the real upstream
store of the day MUST pass once the comparison is identity-based — that is the condition the weekly sync
needs to open its PR.

WHEN the committed store is compared with itself, or with the current upstream store
THEN the guard exits 0 (printing the moved figures as notes) and `make check-registry-keys` is green.

#### Scenario: the vendored store is additive against itself

- **Given** the committed `data/models.json`
- **When** it is compared with a copy of itself
- **Then** no loss is reported
- **Test:** `tests/test_registry_keys.py::test_real_vendored_registry_is_additive_against_itself`

#### Scenario: the current upstream store passes the guard

- **Given** upstream `data/models.json` at `2026-10-26T11:56:20Z` (106 models, 40 engines)
- **When** `python3 scripts/registry_keys.py --cur <that file>` runs against `HEAD:data/models.json`
- **Then** it exits 0 with `OK: additive only — nothing lost`, printing the re-read figures as notes
- **Test:** `python3 scripts/registry_keys.py --cur <upstream>/data/models.json` (live check; the previous
  code exited 1 with 47 findings on the same pair — CI runs the gate via `make check-registry-keys`)
