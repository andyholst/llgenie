# registry-normalise

## ADDED Requirements

### Requirement: the vendored store states formats llgenie can act on

`data/models.json` MUST be written through `sync_registry.normalise()`: every `formats[].name` MUST
be in the vocabulary (`GGUF | MLX | safetensors | mlx-safetensors | litertlm`), in canonical
spelling, without duplicates. A format name outside the vocabulary MUST be dropped, and a row left
with no format MUST state the format its own `hf` repo/id names (`-GGUF` → GGUF, `mlx` → MLX,
`litertlm` → litertlm), else GGUF. Every departure MUST be printed by the sync, never silent.

WHEN upstream writes a model name into `formats[].name`
THEN the vendored store states the format the row's own repo publishes, and the change is named.

#### Scenario: a model name in formats is restated from the repo

- **Given** a row whose only format entry names the model, for a `-GGUF` repo
- **When** the store is normalised
- **Then** the row states `GGUF` for that repo and a note names the row
- **Test:** `tests/test_registry_normalise.py::test_a_model_name_in_formats_name_is_restated_as_the_format_the_repo_states`

#### Scenario: an MLX row is never restated as GGUF

- **Given** a row whose format name is a recipe label and whose repo has no suffix but whose id says MLX
- **When** the store is normalised
- **Then** the row states `MLX`, not the GGUF default
- **Test:** `tests/test_registry_normalise.py::test_an_mlx_row_is_restated_as_mlx_from_its_id_or_repo`

#### Scenario: a real format is canonicalised, never duplicated

- **Given** a row stating the same format twice in different cases
- **When** the store is normalised
- **Then** one canonical entry remains and nothing is reported as dropped
- **Test:** `tests/test_registry_normalise.py::test_a_vocabulary_format_is_kept_and_canonicalised`

### Requirement: rows are kept, duplicates are not

Every upstream model row MUST be kept: a row that looks related to another (a finetune, an MLX
conversion, a run on one box) is a distinct entity upstream and MUST NOT be folded. A row whose id
repeats an earlier row's MUST be dropped, and the drop MUST be printed.

WHEN upstream lists two rows whose names share a prefix
THEN both survive normalisation.

#### Scenario: distinct rows survive, an exact duplicate id is dropped

- **Given** a base model, a finetune of it, and a duplicate of the base id
- **When** the store is normalised
- **Then** the base and the finetune are both present and the duplicate is named as dropped
- **Test:** `tests/test_registry_normalise.py::test_every_distinct_row_is_kept_and_only_a_duplicate_id_is_dropped`

### Requirement: the sync writes the normalised store

`make sync-registry` MUST write the normalised store and the upstream README, and the written file
MUST pass the registry shape check.

WHEN the sync runs against an upstream pair
THEN `data/models.json` holds the normalised row and `validate()` accepts it.

#### Scenario: sync writes a normalised store

- **Given** an upstream store with a non-format `formats[].name` and its README
- **When** the sync runs
- **Then** the written store states `GGUF` for the row's repo and `validate()` accepts the file
- **Test:** `tests/test_registry_normalise.py::test_sync_writes_the_normalised_store_and_check_accepts_it`
