# issue-bodies — spec

Capability: every issue body this repository files, by a bot or by an agent leg, carries the same
human-readable goal, its acceptance criteria and then one technical section (issue #745).

## ADDED Requirements

### Requirement: One renderer produces every issue body

`scripts/issue_body.py::render` MUST be the only place the issue-body section headings are spelled,
and every producer that files an issue MUST render its body through it: `security_issues.body_for`,
`code_review.issue_body`, `run_failure_reactor.issue_body`, `engine_skill_gap.issue_body`,
`registry_change_issue.render`, `architecture_bot.render_issue`, `queued_run_alarm.file_label_issue`.

#### Scenario: a producer renders through the one seam

Given the seven producers the roster in `scripts/issue_body.py::PRODUCERS` names,
When   `make check-issue-bodies` reads their source,
Then   every one imports the renderer and calls it (`issue_body.render(` or the `render_body` alias
       where the module's own function is named `issue_body`), and a producer that hand-builds a
       body is a named failure.

- **Test:** `tests/test_check_issue_body.py::test_a_hand_built_body_fails_the_gate`

#### Scenario: a real finding renders as the six sections

Given a real `security_issues.Finding` (an advisory, a package, a current and a fixed version),
When   `security_issues.body_for(finding)` renders it,
Then   the body's headings are exactly `Problem`, `Why it matters`, `How we fix it`, `Benefit`,
       `Acceptance criteria`, `Technical`, in that order.

- **Test:** `tests/test_security_issues.py::test_the_body_states_advisory_package_versions_and_action`

### Requirement: The sections are ordered, complete, and Technical is last

An issue body MUST carry `## Problem`, `## Why it matters`, `## How we fix it`, `## Benefit`,
`## Acceptance criteria` and `## Technical` in that order. `## Technical` MUST appear nowhere but
last, and the optional `## Not covered` MUST sit between `## Benefit` and `## Technical`. A missing
`problem`, `why`, `benefit`, `how`, `acceptance` or `technical` field MUST make `render` raise.

#### Scenario: a missing section is named

Given a rendered body with no `## Benefit`,
When   `issue_body.missing(body)` is asked what is wrong with it,
Then   it names `Benefit` as missing, and `render()` itself refuses to produce such a body
       (`benefit` is a required field).

- **Test:** `tests/test_issue_body.py::test_a_missing_section_is_named`

#### Scenario: Technical in the middle is refused

Given a body whose `## Technical` precedes its `## Benefit`,
When   `issue_body.missing(body)` reads it,
Then   the order defect is named and `make check-issue-bodies` exits non-zero on it.

- **Test:** `tests/test_issue_body.py::test_technical_must_be_last`

#### Scenario: the out-of-scope list renders before Technical

Given a body rendered with `not_covered=["syft has no image (#746)"]`,
When   the headings are read,
Then   `Not covered` is present, sits before `Technical`, and `Technical` is still the last heading.

- **Test:** `tests/test_issue_body.py::test_not_covered_precedes_technical`

#### Scenario: every readable section is a required field

Given `issue_body.render(...)` called with `problem`, `why` or `benefit` left empty,
When   the call is made,
Then   it raises `ValueError` naming the missing field, instead of emitting a body a reader cannot act
       on.

- **Test:** `tests/test_issue_body.py::test_render_requires_problem_why_benefit`

### Requirement: The issue states its acceptance criteria

`## Acceptance criteria` MUST carry at least one `- [ ]` item — one provable outcome per line, so
"done" is a list a reviewer ticks instead of an adjective. A heading with no tickable item MUST be a
defect in `missing()` and in `make check-issue-bodies`.

#### Scenario: acceptance criteria without a tickable item are refused

Given a rendered body whose `## Acceptance criteria` section carries prose and no `- [ ]` item,
When   `issue_body.missing(body)` reads it and `make check-issue-bodies` runs,
Then   both name the missing tickable criterion.

- **Test:** `tests/test_issue_body.py::test_acceptance_criteria_must_be_tickable`

#### Scenario: the renderer refuses a body with no acceptance criteria

Given `issue_body.render(...)` called with no `acceptance`,
When   the call is made,
Then   it raises `ValueError`, exactly as it does for a missing `problem`/`why`/`benefit`.

- **Test:** `tests/test_issue_body.py::test_render_requires_acceptance`

#### Scenario: every producer renders tickable criteria

Given a real security finding, a real code-review finding, a real failed run, a real unskilled engine
and a real registry change,
When   their scripted producers render the body,
Then   each body carries the six sections and at least one `- [ ]` item.

- **Test:** `tests/test_issue_body.py::test_every_producer_renders_tickable_criteria`

### Requirement: The dedupe marker survives the shape

WHEN a producer passes its marker to the renderer, THEN the marker MUST be the body's first line,
unchanged, so `security_issues`' `MARKER_RE`, `code_review.filed()`, `run_failure_reactor.filed()`,
`registry_change_issue`'s marker search and `queued_run_alarm`'s label marker all still find the issue
they filed and update it instead of filing a duplicate.

#### Scenario: one advisory is filed once

Given a body rendered with the marker `<!-- security-finding: trivy:GHSA-x:pkg -->`,
When   `security_issues.MARKER_RE` reads the body and a second `apply()` runs on the same finding,
Then   the marker round-trips to the same key and the second run plans an update, not a create.

- **Test:** `tests/test_issue_body.py::test_the_marker_round_trips`

### Requirement: The gate refuses a lost rule, not just a bad body

`make check-issue-bodies` MUST also fail when `AGENTS.md` no longer carries the section stating the
shape, or when `.hermes/skills/issue-triage/SKILL.md` / `.hermes/skills/issue-refiner/SKILL.md` no
longer name the six sections — so deleting the rule is a red gate instead of a silent edit.

#### Scenario: deleting the AGENTS.md section reds the gate

Given an `AGENTS.md` with the section removed,
When   `make check-issue-bodies` runs,
Then   it exits non-zero and names the missing section.

- **Test:** `tests/test_check_issue_body.py::test_a_lost_agents_section_fails`

#### Scenario: an issue skill that stopped stating the shape fails

Given an `issue-refiner/SKILL.md` whose `## Output` no longer names `## Acceptance criteria`,
When   `make check-issue-bodies` runs,
Then   it exits non-zero and names the skill file.

- **Test:** `tests/test_check_issue_body.py::test_an_issue_skill_without_the_shape_fails`

#### Scenario: the renderer and the checker agree

Given the renderer's canonical body,
When   its own `missing()` reads it,
Then   it conforms — otherwise the gate would be decoration.

- **Test:** `tests/test_check_issue_body.py::test_the_renderer_and_the_checker_agree`

### Requirement: The agent legs restate in the same shape

WHEN the `issue-triage` leg answers `refine`, or the `issue-refiner` leg answers `refined`, THEN the
`REFINED:` / `RESTATED:` block they write MUST carry the six sections in order, ending with
`Technical`, so a human-written issue reaches the implementer with a stated goal and tickable
acceptance criteria.

#### Scenario: the refiner's restatement carries the shape

Given the refiner skill's `## Output` block,
When   the shape it prescribes is read,
Then   it names all six sections, requires `Technical` last, and requires `- [ ]` acceptance criteria.

- **Test:** `tests/test_check_issue_body.py::test_an_issue_skill_without_the_shape_fails`
