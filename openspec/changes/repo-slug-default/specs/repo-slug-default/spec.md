# repo-slug-default

## ADDED Requirements

### Requirement: gh receives a slug, never the checkout path

Every Makefile recipe that passes `--repo` to `gh` MUST pass `$(GH_REPO)`: the repository slug when
`REPO` is the checkout path, or an explicit `REPO=owner/name` override.

WHEN a documented bot target runs without `REPO=`
THEN the gh call carries `asimov-agent/llgenie`.

#### Scenario: the documented invocation works

- **Given** `make issue-cleaner-scan` with no `REPO=`
- **When** make expands it
- **Then** the gh call names `asimov-agent/llgenie` and not the checkout path
- **Test:** `tests/test_repo_slug.py::test_the_documented_invocations_carry_the_slug`

#### Scenario: an explicit override still wins

- **Given** `make issue-cleaner-scan REPO=owner/name`
- **When** make expands it
- **Then** the override is what gh receives
- **Test:** `tests/test_repo_slug.py::test_an_explicit_repo_override_still_wins`

#### Scenario: no recipe keeps the path form

- **Given** the Makefile
- **When** every `--repo` argument is read
- **Then** none of them is `$(REPO)`
- **Test:** `tests/test_repo_slug.py::test_no_recipe_passes_the_checkout_path_to_gh`
