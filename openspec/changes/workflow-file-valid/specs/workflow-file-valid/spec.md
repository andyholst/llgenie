# workflow-file-valid

## ADDED Requirements

### Requirement: a workflow file GitHub refuses is a CI failure

Every tracked `.github/workflows/*.yml` SHALL be a file GitHub ACCEPTS. A file whose `${{ … }}`
expression does not parse SHALL fail `make check-workflows` (the `ci-unit` gate), because GitHub
refuses the whole file and reports it only as a run with zero jobs named after the file path.

#### Scenario: the expression that shipped is reported

- **GIVEN** a workflow whose `run: |` block carries a comment with a literal `${{ ... }}`,
- **WHEN** `check_workflows.py` reads it,
- **THEN** it reports `bad-expression` naming the file and the line that carries it.

- **Test:** `tests/test_workflows_valid.py::test_the_guard_fires_on_the_expression_that_shipped`

#### Scenario: a real expression inside a run block is accepted

- **GIVEN** a workflow whose `run: |` block interpolates a valid expression
  (`${{ inputs.dry || 'false' }}`),
- **WHEN** the guard reads it,
- **THEN** it reports nothing — the rule is a parser, not a `${{` grep.

- **Test:** `tests/test_workflows_valid.py::test_a_valid_expression_is_accepted`

#### Scenario: an unterminated expression is reported

- **GIVEN** a workflow whose `run:` block opens `${{` and never closes it,
- **WHEN** the guard reads it,
- **THEN** it reports `unterminated`.

- **Test:** `tests/test_workflows_valid.py::test_an_unterminated_expression_is_a_violation`

### Requirement: a duplicate key and a missing name are refusals too

A workflow mapping with the same key twice SHALL be reported as `duplicate-key`, and a workflow with
no top-level `name:` SHALL be reported as `missing-name`.

#### Scenario: a duplicate key is reported

- **GIVEN** a workflow that sets the same key twice in one mapping,
- **WHEN** the guard reads it with the strict loader,
- **THEN** it reports `duplicate-key`.

- **Test:** `tests/test_workflows_valid.py::test_a_duplicate_key_is_a_violation`

#### Scenario: a workflow with no name is reported

- **GIVEN** a workflow file with no top-level `name:`,
- **WHEN** the guard reads it,
- **THEN** it reports `missing-name`.

- **Test:** `tests/test_workflows_valid.py::test_a_workflow_without_a_name_is_a_violation`

### Requirement: this repository's workflow files all parse

Every workflow file in this repository SHALL parse as strict YAML with no duplicate keys, carry a
top-level `name:`, and end with a newline; and the file that was refused SHALL no longer carry a
literal expression.

#### Scenario: the repository is clean

- **GIVEN** the repository's `.github/workflows/` tree,
- **WHEN** the guard and the strict-YAML assertion run,
- **THEN** there are no violations and `check_workflows.py check` exits 0.

- **Test:** `tests/test_workflows_valid.py::test_this_repository_has_no_refused_workflow_file`,
  `tests/test_workflows_valid.py::test_every_workflow_parses_as_strict_yaml_with_no_duplicate_keys`

#### Scenario: the refused file is fixed

- **GIVEN** `.github/workflows/engine-bump-rebase.yml`,
- **WHEN** it is read,
- **THEN** it carries no literal `${{ ... }}`.

- **Test:** `tests/test_workflows_valid.py::test_the_shipped_file_no_longer_carries_a_literal_expression`

### Requirement: the guard is wired into the pipeline

`make check-workflows` SHALL exist, be declared `.PHONY`, appear in `make help`, run in the `ci-unit`
recipe, and its test file SHALL be named by `test-unit` — a guard no target names runs nowhere.

#### Scenario: the guard runs in CI and its test runs with the unit suite

- **GIVEN** the `Makefile`,
- **WHEN** its target list, `.PHONY`, help text, `ci-unit` and `test-unit` recipes are read,
- **THEN** all five name the guard (and `tests/test_workflows_valid.py`).

- **Test:** `tests/test_workflows_valid.py::test_the_guard_is_wired_into_the_repo`
