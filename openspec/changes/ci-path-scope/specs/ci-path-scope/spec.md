# ci-path-scope

## ADDED Requirements

### Requirement: a diff is classified once, into named classes
One classifier MUST map a diff's paths to change classes, MUST select every class when a wildcard path is
touched, and MUST fail naming the path when no class claims it.

WHEN a diff is classified
THEN every path maps to at least one class, or the run exits non-zero naming the path
AND a wildcard path (`Makefile`, `tools/**`, `.github/**`, `scripts/ci_*.py`, `scripts/engine_*.py`,
`scripts/check_*.py`, `pytest.ini`, `.gitleaks.toml`, `renovate.json`, `AGENTS.md`) selects every class.

#### Scenario: an unmatched path is loud
- **Given** a diff containing `mystery/file.txt`
- **When** the classifier runs
- **Then** it exits 1 and the message names that path
- **Test:** `tests/test_ci_scope.py::test_the_cli_exits_non_zero_and_names_the_unmatched_path`

#### Scenario: a wildcard beside a docs file selects everything
- **Given** `docs/ARCHITECTURE.md` and `AGENTS.md`
- **When** the classifier runs
- **Then** every class is selected
- **Test:** `tests/test_ci_scope.py::test_a_wildcard_wins_even_beside_a_docs_path`

### Requirement: the docs class is selected at the trigger
`ci.yml` MUST ignore a docs-only diff on `pull_request` and MUST NOT filter `push`; the ignored list MUST
be the `docs` class minus its wildcards.

WHEN a PR's diff is only docs paths
THEN `ci.yml` starts no run
AND `scope.yml` runs the docs gates and reports one check named `scope`
AND a `push` to `main` still runs the whole matrix.

#### Scenario: the YAML and the classifier cannot drift
- **Given** `scripts/ci_scope.py::DOCS_TRIGGER_IGNORE`
- **When** the test reads `ci.yml`'s `pull_request.paths-ignore`
- **Then** the two are equal, and `push` carries no path filter
- **Test:** `tests/test_ci_scope.py::test_ci_yml_ignores_exactly_the_docs_trigger_list`

#### Scenario: the scope workflow is always present
- **Given** `.github/workflows/scope.yml`
- **When** the test reads it
- **Then** its `pull_request` trigger has no `paths`/`paths-ignore`, its single job is `scope`, it runs
  `scripts/ci_scope.py` and the docs gates, and its only `uses:` is the pinned checkout
- **Test:** `tests/test_ci_scope.py::test_the_scope_workflow_has_no_path_filter_and_runs_the_docs_gates`

### Requirement: the job table describes the workflow that exists
The classifier's job table MUST name only jobs `ci.yml` actually defines.

WHEN the table and the workflow disagree
THEN the test fails, naming the jobs the classifier invented
- **Test:** `tests/test_ci_scope.py::test_every_job_the_classifier_names_exists_in_ci_yml`

#### Scenario: a docs-only diff selects fewer than ten jobs
- **Given** a diff of `docs/ARCHITECTURE.md` and `CHANGES.md`
- **When** the classifier selects jobs
- **Then** fewer than ten run, `guard`/`linux/lint`/`linux/openspec` among them
- **And** every skipped job's line states the class it would have needed
- **Test:** `tests/test_ci_scope.py::test_a_docs_only_diff_selects_fewer_than_ten_jobs_and_names_what_it_skipped`
