## ADDED Requirements

### Requirement: select-refuses-an-unknown-class

`scripts/ci_scope.py::select()` SHALL raise `ValueError`, naming the unknown entries and the valid
class names, when any entry of its `classes` argument is not a key of `CLASSES`. An empty `classes`
list SHALL stay legal and select only the always-on jobs, and a list of real classes SHALL select
exactly the jobs it selected before the guard.

#### Scenario: a mistyped class is a loud caller bug

- **Given** `select()` and a class list containing `tests_typo`, which is not a key of `CLASSES`
- **When** `select(["tests_typo"])` is called
- **Then** it raises `ValueError` whose message contains `tests_typo` and the valid class names
- **And** no job rows are returned, so no caller can render a quiet 2-of-10 selection
- **Test:** `tests/test_ci_scope.py::test_select_refuses_an_unknown_class_naming_it_and_the_valid_set`

#### Scenario: every unknown entry is named, not just the first

- **Given** a class list with more than one name that is not a key of `CLASSES`
- **When** `select()` is called
- **Then** the `ValueError` message names each unknown entry
- **Test:** `tests/test_ci_scope.py::test_select_names_every_unknown_entry_not_just_the_first`

#### Scenario: an empty class list stays the always-on selection

- **Given** the documented `--paths ''` case, where nothing was read
- **When** `select([])` is called
- **Then** it returns rows without raising, and exactly the always-on jobs are selected
- **Test:** `tests/test_ci_scope.py::test_select_an_empty_class_list_is_legal_and_selects_the_always_on_jobs`

#### Scenario: a full class list still selects every job

- **Given** every real class name
- **When** `select(list(CLASSES))` is called
- **Then** it returns one row per job of `ci.yml` and every row is selected (`10/10`)
- **Test:** `tests/test_ci_scope.py::test_select_every_real_class_still_returns_every_job`
