## ADDED Requirements

### Requirement: The bot takes ONE eligible issue, deterministically

`make security-bot` MUST select exactly one open issue carrying `security`, `vulnerability` and
`auto-fixable` — the oldest by creation time — and MUST do nothing when none is eligible.

#### Scenario: the oldest eligible issue wins

Given three open issues, two eligible and one without `auto-fixable`,
When   the bot selects,
Then   it takes the older of the two eligible ones.

- **Test:** `tests/test_security_bot.py::test_select_takes_the_oldest_auto_fixable_issue`

#### Scenario: no eligible issue is a quiet no-op

Given no open issue carrying the three labels,
When   the bot runs,
Then   it reports nothing to do and exits 0.

- **Test:** `tests/test_security_bot.py::test_select_returns_none_when_nothing_is_eligible`

### Requirement: The fix is parsed from the issuer's body, or refused

The bot MUST read the package and the `current -> fixed` line from the issue body format #716
writes. A body without those lines MUST be refused, never guessed.

#### Scenario: the issuer's body parses

Given an issue body written by `make security-issues`,
When   it is parsed,
Then   the package, the current version, the fixed version and the marker come out.

- **Test:** `tests/test_security_bot.py::test_parse_reads_package_and_versions_from_the_issuer_body`

#### Scenario: an unparseable body is refused

Given an issue body with no package line,
When   it is parsed,
Then   the bot refuses with a message naming the format contract.

- **Test:** `tests/test_security_bot.py::test_parse_refuses_a_body_without_the_lines`

### Requirement: Only the source-of-truth pin is edited

The bot MUST edit the pin in `tools/requirements*.in` and MUST NOT edit a compiled
`requirements*.txt`. A package pinned in neither MUST produce no edit.

#### Scenario: the plan names the .in line

Given a checkout whose `tools/requirements.in` pins the package,
When   the plan is computed,
Then   it names that file, the old line and the new one.

- **Test:** `tests/test_security_bot.py::test_apply_plan_finds_the_pin_and_leaves_compiled_files_alone`

#### Scenario: an unknown package produces no edit

Given a finding for a package no `.in` pins,
When   the plan is computed,
Then   there is no edit to make.

- **Test:** `tests/test_security_bot.py::test_a_package_pinned_nowhere_is_refused`

### Requirement: Green or nothing

Before a branch is pushed the fast gates MUST pass. When a gate is red the bot MUST revert the edit,
comment the real output on the issue, and open NO PR. A container advisory or an unpinned package
MUST be commented as a refusal rather than guessed at.

#### Scenario: a red gate leaves no PR

Given a checkout whose fast gates fail,
When   the bot applies,
Then   it reverts the pin, comments the gate output on the issue, and creates no PR.

- **Test:** `tests/test_security_bot.py::test_red_gates_revert_the_edit_and_open_no_pr`

#### Scenario: a container advisory is refused

Given a finding whose component is a container,
When   the plan is computed,
Then   there is no editable pin and the bot comments instead of guessing.

- **Test:** `tests/test_security_bot.py::test_a_container_finding_is_refused_not_guessed`

### Requirement: A green run pushes one branch and opens one PR

When the gates are green the bot MUST push `fix/security-<advisory>-<package>` with one commit, and
open a PR whose body carries `Issue:`, `Fix:`, `Benefit:`, `Technical:` and `closes #<issue>`. It
MUST never merge, never push to `main`, and never force-push.

#### Scenario: the happy path

Given a clean checkout and an eligible issue,
When   the bot applies,
Then   the pin moves, the branch is on `origin`, the PR body carries the four parts and closes the
       issue, and no merge is attempted.

- **Test:** `tests/test_security_bot.py::test_green_gates_edit_push_and_open_the_pr`

#### Scenario: a dry run writes nothing

Given `DRY=1`,
When   the bot runs,
Then   the file is unchanged and nothing is pushed or opened.

- **Test:** `tests/test_security_bot.py::test_dry_run_writes_nothing`

### Requirement: The bot's contract with the issuer is gated

`make check-security-bot` (inside `make ci-unit`) MUST fail when a select label is missing from the
issuer's roster, when a pin source is missing, or when a compiled `requirements*.txt` becomes an
edit target.

#### Scenario: the shipped contract is sane

Given this repository,
When   `make check-security-bot` runs,
Then   it exits 0 naming the select labels and the two `.in` sources.

- **Test:** `tests/test_security_bot.py::test_the_real_contract_is_sane`
