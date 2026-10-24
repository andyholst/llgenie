# engine-params-review

## ADDED Requirements

### Requirement: A proposal is applied only when the documentation proves it

The apply step SHALL accept a proposed build parameter only when the backend is one the engine builds
(or `common`), the named upstream file exists at the pinned sha, the flag's `NAME` appears in that file,
the quoted evidence is a substring of that file, and the flag is not already in the params. Every other
proposal SHALL be dropped and reported with its reason, never applied.

WHEN the review leg hands `params-review.md` to the host
THEN each `PROPOSE` line is validated against the upstream tree before anything is written.

#### Scenario: a documented arch-specific flag is applied to its backend

Given a proposal for `cuda` whose flag and quote are both in the upstream `CMakeLists.txt`
When  the proposals are validated and applied
Then  the flag is appended to `cmake_flags.cuda` in the skill and the other backends are untouched.

- **Test:** `tests/test_engine_params_review.py::test_a_documented_arch_flag_is_proposed_and_applied`

#### Scenario: an undocumented flag is dropped

Given a proposal whose flag appears nowhere in the named file
When  the proposals are validated
Then  nothing is applied and the drop names the flag and the file.

- **Test:** `tests/test_engine_params_review.py::test_an_undocumented_proposal_is_dropped`

#### Scenario: a quote that is not in the document is dropped

Given a proposal whose quoted evidence is not a substring of the named file
When  the proposals are validated
Then  it is dropped for the evidence, not for the flag.

- **Test:** `tests/test_engine_params_review.py::test_a_quote_that_is_not_in_the_document_is_dropped`

#### Scenario: a backend the engine does not build is rejected

Given a proposal naming a backend outside the skill's `backends` and `common`
When  the proposals are validated
Then  it is rejected, naming the backends the engine does build.

- **Test:** `tests/test_engine_params_review.py::test_a_backend_the_engine_does_not_build_is_rejected`

#### Scenario: a flag already in the params is rejected

Given a proposal whose flag the skill already builds with
When  the proposals are validated
Then  it is rejected as already present.

- **Test:** `tests/test_engine_params_review.py::test_a_flag_already_in_the_params_is_rejected`

### Requirement: The host writes, the agent only proposes

The engine's `SKILL.md` SHALL remain the only writer of parameters: accepted flags are appended to
`cmake_flags.<backend>` and `make generate-engine-params` regenerates the params and Dockerfiles. A
`DRY=1` run SHALL report the same decision and mutate nothing.

WHEN an accepted flag is applied
THEN the skill carries it and the generated files are regenerated from the skill.

#### Scenario: a dry run mutates nothing

Given an accepted proposal and an unchanged skill
When  the apply step runs with `DRY=1`
Then  it reports what it would change and the skill file is byte-identical.

- **Test:** `tests/test_engine_params_review.py::test_a_dry_apply_writes_nothing`

### Requirement: The bump PR carries the review's outcome

The PR SHALL gain a `Documentation review` section listing every applied parameter with the doc it
came from, and every refused proposal with its reason. A review that proposes nothing SHALL say so.

WHEN the review step finishes
THEN `params-review-section.md` describes both sides and the bump workflow appends it to the PR body.

#### Scenario: the section names what was applied and what was dropped

Given one accepted and one refused proposal
When  the PR section is built
Then  it carries the applied flag with its document and the refusal with its reason.

- **Test:** `tests/test_engine_params_review.py::test_the_section_names_what_was_applied_and_what_was_dropped`

#### Scenario: a review that proposes nothing says so

Given no proposals
When  the PR section is built
Then  it states that no documentation-sourced parameter was proposed.

- **Test:** `tests/test_engine_params_review.py::test_a_review_that_proposes_nothing_says_so`

### Requirement: The review leg never blocks the bump

The workflow step SHALL run after `make engine-bump` and before the PR is opened, and SHALL NOT fail
the job: a review that errors or proposes nothing still opens the PR with the outcome in its body.

WHEN the review leg fails for an engine
THEN the job continues, the PR is opened, and the run emits a warning naming the engine.

#### Scenario: the step is non-fatal and ordered before the PR

Given the engine-bump workflow's bump job
When  its steps are read
Then  the review step is `continue-on-error`, sits before the PR step, and the PR step appends the section.

- **Test:** `tests/test_engine_params_review.py::test_the_bump_workflow_runs_the_review_before_the_pr`
