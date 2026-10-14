# llgenie-serve-naming

## ADDED Requirements

### Requirement: The CLI module is named after the project

The CLI module SHALL be `scripts/llgenie_serve.py`. No live file — source, test, Makefile,
workflow, container file or documentation — SHALL name it `llama_serve`, and the guard test
SHALL fail listing the offending files if one does.

#### Scenario: no live reference to the old module name

- **WHEN** every live text file is searched for the old module name
- **THEN** none SHALL match, except the compatibility shim, the dated history under
  `agent-wiki/`, merged `openspec/changes/`, and the guard test itself

#### Scenario: upstream's names are not collateral damage

- **WHEN** the tree is searched for `llama-server`, `build_llama_server.sh`, `LLAMA_SERVER` and
  `LLAMA_CUBLAS`
- **THEN** each SHALL still be present, because they name llama.cpp, not llgenie

### Requirement: The old module path keeps working for one release

`scripts/llama_serve.py` SHALL remain importable and executable as a deprecated alias: importing
it SHALL yield the same module object as `scripts.llgenie_serve`, and running it SHALL run the
CLI. The shim SHALL be removed in a follow-up once the alias has served its release.

#### Scenario: importing the old path yields the real module

- **WHEN** both paths are imported in one process
- **THEN** they SHALL be the same object, so attribute and function identities match

#### Scenario: running the old path runs the CLI

- **WHEN** the old path is executed with `--help`
- **THEN** it SHALL exit 0 and print the CLI usage

### Requirement: llgenie's own environment seams are named after llgenie

Every environment knob that belongs to llgenie (not to a served engine) SHALL have an
`LLGENIE_*` name that takes precedence, with the legacy `LLAMA_*` spelling still honoured as a
deprecated alias. Both spellings SHALL be exercised by tests, and the recorded alias table SHALL
contain only pairs the code actually reads.

#### Scenario: the new spelling wins

- **GIVEN** both `LLGENIE_BACKEND` and `LLAMA_BACKEND` are set
- **WHEN** the backend is detected
- **THEN** the `LLGENIE_BACKEND` value SHALL be used

#### Scenario: the legacy spelling still works

- **GIVEN** only `LLAMA_BACKEND` (or only `LLAMA_RAM_BYTES`) is set
- **WHEN** detection runs
- **THEN** it SHALL behave exactly as before the rename

#### Scenario: an empty new value falls back to the alias

- **GIVEN** `LLGENIE_BACKEND` is set to the empty string and `LLAMA_BACKEND` to a value
- **WHEN** the seam is read
- **THEN** the alias value SHALL be used, because an empty string means "unset"

### Requirement: The installed artifacts follow the new path

`make install` SHALL write a launcher that runs `scripts/llgenie_serve.py` and a `~/bin/llgenie.py`
symlink pointing at it, and `make uninstall`'s "repo untouched" assertion SHALL check the new
path. A real host install SHALL be part of the verification.

#### Scenario: a fresh install points at the new module

- **WHEN** the launcher and the symlink are regenerated on a host
- **THEN** both SHALL name `scripts/llgenie_serve.py`

#### Scenario: the plan a user sees is unchanged

- **WHEN** `--dry` is run for a llama.cpp engine and for an engine that is not llama.cpp
- **THEN** the printed plans SHALL be identical to the ones printed before the rename
