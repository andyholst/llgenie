# params-review-budget

## ADDED Requirements

### Requirement: The brief is a ranked selection bounded in total

`brief` SHALL exclude non-build trees, take the flag-proving files first within their own share of the
budget, then the remaining documents highest build-relevance first, until a total budget, and SHALL print
how many files that budget left out.

WHEN the documents at an engine's pin are gathered
THEN the brief is a bounded, build-relevance-ranked selection and says so.

#### Scenario: bench pages are excluded and the total is bounded

Given an upstream tree dominated by benchmark result pages and prose
When  the brief gathers its documentation
Then  no `bench/` page is included, the total stays within the budget, and the omitted count is reported.

- **Test:** `tests/test_engine_params_review.py::test_the_brief_selects_by_build_relevance_and_says_what_it_dropped`

### Requirement: A flag-proving file is not cut before its options

The root `CMakeLists.txt` and the backend Dockerfiles SHALL be selected before other documents and SHALL
be allowed a larger per-file cap than a prose page, so the lines that prove a flag are not truncated away.

WHEN the selection reaches the root `CMakeLists.txt`
THEN its content is carried past the prose per-file cap, including its last `option(...)` line.

#### Scenario: the last option survives the cap

Given a root `CMakeLists.txt` larger than the prose per-file cap, full of `option(...)` lines
When  it is selected
Then  its last option line is present in the brief.

- **Test:** `tests/test_engine_params_review.py::test_the_brief_selects_by_build_relevance_and_says_what_it_dropped`

### Requirement: `docs/` root-level pages are scanned

The documentation globs SHALL match a page directly under `docs/`, not only one in a subdirectory.

WHEN the upstream tree carries `docs/BUILDING.md`
THEN it is a candidate for the brief.

#### Scenario: a docs-root page outranks prose

Given one `docs/BUILDING.md` and many prose pages in subdirectories
When  the brief gathers its documentation
Then  the docs-root page is selected and prose is what the budget leaves out.

- **Test:** `tests/test_engine_params_review.py::test_a_build_document_outranks_prose_and_docs_root_is_scanned`
