# Tasks — workflow-file-valid

## The refused file

- [x] Reword the comment inside `engine-bump-rebase.yml`'s `run: |` block so no literal `${{ ... }}`
      remains (the comment is script text, so GitHub parsed it as an expression).

## The gate

- [x] Add `scripts/check_workflows.py` with `check` / `report`, failing on `bad-expression`,
      `unterminated`, `duplicate-key` and `missing-name`.
- [x] Add `make check-workflows` + `make workflows-report`, declare both in `.PHONY`, list
      `check-workflows` in `make help`, and run it from `ci-unit`.
- [x] Name `tests/test_workflows_valid.py` in the `test-unit` recipe.

## Tests (no mocks; the real script and the real workflow files)

- [x] `tests/test_workflows_valid.py::test_the_guard_fires_on_the_expression_that_shipped`
- [x] `tests/test_workflows_valid.py::test_a_valid_expression_is_accepted`
- [x] `tests/test_workflows_valid.py::test_an_unterminated_expression_is_a_violation`
- [x] `tests/test_workflows_valid.py::test_a_duplicate_key_is_a_violation`
- [x] `tests/test_workflows_valid.py::test_a_workflow_without_a_name_is_a_violation`
- [x] `tests/test_workflows_valid.py::test_this_repository_has_no_refused_workflow_file`
- [x] `tests/test_workflows_valid.py::test_every_workflow_parses_as_strict_yaml_with_no_duplicate_keys`
- [x] `tests/test_workflows_valid.py::test_the_shipped_file_no_longer_carries_a_literal_expression`
- [x] `tests/test_workflows_valid.py::test_the_guard_is_wired_into_the_repo`
- [x] `tests/test_workflows_valid.py::test_the_script_runs_as_a_cli_and_reports`
- [x] Rule-6c proof: 3 of the tests fail on the pre-fix tree (the unfixed workflow file, the
      repo-wide check, the wiring check) and all 10 pass after the fix.

## Docs and record

- [x] Update `README.md` for the new targets.
- [x] State the rule in `AGENTS.md` (a `#` inside `run:` is script text; a refused file shows up as a
      0-job run named after its path).
- [x] Write the work record `agent-wiki/2026-10-16-workflow-file-valid.md`.
- [x] Note on #330 that this change implements it, and that #318 is superseded by it.

## OpenSpec

- [x] `proposal.md`, `specs/workflow-file-valid/spec.md`, `tasks.md` written.
- [x] `make openspec-validate NAME=workflow-file-valid` passes.

## Gates

- [x] `make lint` passes.
- [x] `make check-workflows` passes.
- [x] `make check-wiring` and `make check-docs` pass.
- [x] The rest of the loop runs in CI on this branch.
