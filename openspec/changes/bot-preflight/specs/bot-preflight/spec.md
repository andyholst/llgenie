# bot-preflight

## ADDED Requirements

### Requirement: a leg proves its tree contains current `main` before it starts work

`make bot-preflight` MUST fetch `origin/main` before doing anything else, and MUST refuse to proceed
unless the checkout contains that commit. A checkout **at** `main` MUST pass, a **behind** checkout
MUST be fast-forwarded (`git merge --ff-only`, never a rebase, never a reset), and a **diverged**
checkout MUST be refused with the `git rev-list --left-right --count` numbers printed. A fetch
failure, a dirty working tree, or an `origin` remote whose GitHub slug is not `asimov-agent/llgenie`
MUST also be refused. Every refusal exits **2** and names what it read.

WHEN a leg runs the preflight
THEN the tree contains `origin/main`, or the run stops with exit 2 and the reason.

#### Scenario: a clean checkout at `main` passes

- **Given** a clone whose `HEAD` is already the commit `origin/main` names
- **When** the preflight runs
- **Then** it exits 0, reports the tree is at `main`, and writes `preflight.txt`
- **Test:** `tests/test_bot_preflight.py::test_a_clean_checkout_at_main_passes_and_records_the_line`

#### Scenario: a clean behind checkout is fast-forwarded

- **Given** a clone one commit behind `origin/main`, with no local change
- **When** the preflight runs
- **Then** it exits 0 and `HEAD` is `origin/main` afterwards
- **Test:** `tests/test_bot_preflight.py::test_a_clean_behind_checkout_is_fast_forwarded`

#### Scenario: a dirty checkout refuses and names the paths

- **Given** a clone behind `origin/main` with an uncommitted edit
- **When** the preflight runs
- **Then** it exits 2, the message names the edited path, and `HEAD` has not moved
- **Test:** `tests/test_bot_preflight.py::test_a_dirty_checkout_refuses_and_names_the_paths`

#### Scenario: a branch ahead of `main` passes

- **Given** a clone with one commit of its own on top of `origin/main`
- **When** the preflight runs
- **Then** it exits 0, `HEAD` is untouched, and the record says the tree is ahead
- **Test:** `tests/test_bot_preflight.py::test_a_branch_ahead_of_main_passes`

#### Scenario: a diverged checkout refuses with the counts

- **Given** a clone whose branch has a commit `origin/main` does not contain
- **When** the preflight runs
- **Then** it exits 2 and prints the `git rev-list --left-right --count HEAD...origin/main` numbers
  as `<HEAD-only> (HEAD-only) <main-only> (main-only)`
- **Test:** `tests/test_bot_preflight.py::test_a_diverged_checkout_refuses_and_prints_the_counts`

#### Scenario: an origin that is not this repository refuses

- **Given** a clone whose `origin` is a GitHub URL of a different repository
- **When** the preflight runs
- **Then** it exits 2 and names the slug it read
- **Test:** `tests/test_bot_preflight.py::test_an_origin_that_is_not_this_repository_refuses`

#### Scenario: an unreachable remote is a failure, never a stale start

- **Given** a clone whose `origin` cannot be fetched
- **When** the preflight runs
- **Then** it exits 2 and names the fetch failure
- **Test:** `tests/test_bot_preflight.py::test_an_unreachable_remote_refuses`

### Requirement: the preflight records the rulebook it read

The preflight MUST write `preflight.txt` at the repository root, a run input that is gitignored and
never committed. It MUST carry the line `AGENTS: <main sha> <bytes>b <lines>l` — the exact line a PR
body repeats — plus a `sha256` digest of the `## ` headings of `AGENTS.md`, so a prose edit does not
change the digest while a rule change does. The counts and the digest MUST be read from `AGENTS.md`
at **that sha** (`git show <sha>:AGENTS.md`), so a branch that edits the rulebook still writes a line
its own hygiene gate accepts; only when the object is absent MAY the working tree be read, and the
source MUST be stated. `--check` MUST re-read an existing file against live values and print the
**first** difference instead of passing.

WHEN the preflight has verified the tree
THEN `preflight.txt` states the sha, the byte size, the line count and the heading digest it read,
and a stale file is named by `--check` with the field that disagrees.

#### Scenario: the recorded line names the rulebook

- **Given** a checkout at `main`
- **When** the preflight runs
- **Then** the first line of `preflight.txt` is `AGENTS: <sha> <bytes>b <lines>l` for that
  `AGENTS.md`, and the file also carries the heading digest
- **Test:** `tests/test_bot_preflight.py::test_a_clean_checkout_at_main_passes_and_records_the_line`

#### Scenario: the counts come from the rulebook at the recorded sha

- **Given** a branch ahead of `main` that edits `AGENTS.md`
- **When** the preflight runs
- **Then** the `AGENTS:` line names `main`'s sha with `AGENTS.md` counts at that sha, not the branch's
  copy, and the printed source names the object it read
- **Test:** `tests/test_bot_preflight.py::test_a_branch_that_edits_agents_records_the_rulebook_at_main`

#### Scenario: the heading digest follows the rules, not the prose

- **Given** a recorded `preflight.txt`
- **When** a sentence inside an existing section of `AGENTS.md` is reworded
- **Then** the digest is unchanged, and adding a `## ` heading changes it
- **Test:** `tests/test_bot_preflight.py::test_the_heading_digest_follows_the_rule_headings_not_the_prose`

#### Scenario: a stale record is caught before anything is written

- **Given** a `preflight.txt` whose recorded main sha is not the live `origin/main`
- **When** the preflight runs with `--check`
- **Then** it exits 2 and prints the field and both values
- **Test:** `tests/test_bot_preflight.py::test_check_mode_names_the_first_difference_against_a_stale_file`

#### Scenario: the record is never repo content

- **Given** the repository's `.gitignore`
- **When** `preflight.txt` is created at its root
- **Then** `git status --porcelain` does not list it
- **Test:** `tests/test_bot_preflight.py::test_preflight_txt_is_gitignored`

### Requirement: a PR body cites the `AGENTS.md` the work obeyed

`make check-pr-hygiene` MUST reject a bot PR body that does not carry the `AGENTS:` line, whose sha
is not a `main` commit the PR contains (an ancestor of both `HEAD` and the base), or whose byte and
line counts are not those of `AGENTS.md` at **that** sha. A PR is a **bot PR** when every commit it adds is authored by the bot identity
(`Asimov Agent <support@docondee.com>`); a human-authored PR MUST NOT be failed for a rule stated
nowhere a person reads. It MUST read the body without network when one is available — `--pr-body-file`,
`$PR_BODY_FILE`, `$GITHUB_EVENT_PATH`'s `pull_request.body` — and MUST read it through `gh` only when
`PR=`/`REPO=` are passed explicitly. On a push to `main`, where no PR body exists, the rule MUST
report that it read no body and MUST NOT fail.

WHEN the hygiene gate reads a PR body
THEN the `AGENTS:` line matches the merge-base sha and that sha's `AGENTS.md`, or the gate fails
naming the field that disagrees.

#### Scenario: a body with the matching line passes

- **Given** a PR body whose `AGENTS:` line names the merge-base sha and that sha's `AGENTS.md`
- **When** `check-pr-hygiene` reads it
- **Then** no `pr-agents-line` finding is reported
- **Test:** `tests/test_pr_hygiene.py::test_a_pr_body_with_the_matching_agents_line_passes`

#### Scenario: a body without the line is rejected

- **Given** a PR body carrying `Issue:`/`Fix:`/`Benefit:`/`Technical:` and no `AGENTS:` line
- **When** `check-pr-hygiene` reads it
- **Then** it reports a missing-line finding naming the expected shape
- **Test:** `tests/test_pr_hygiene.py::test_a_pr_body_without_the_agents_line_is_a_violation`

#### Scenario: a sha the PR does not contain is rejected

- **Given** a PR body whose `AGENTS:` sha is not an ancestor of the PR head or of the base
- **When** `check-pr-hygiene` reads it
- **Then** it reports a finding naming the sha and the current merge base
- **Test:** `tests/test_pr_hygiene.py::test_a_pr_body_whose_agents_sha_the_pr_does_not_contain_is_a_violation`

#### Scenario: a rebase that moved main does not invalidate the line

- **Given** a PR body citing an older `main` commit that the branch and `origin/main` both contain
- **When** `check-pr-hygiene` reads it after `rebase-bot` moved the merge base
- **Then** no `pr-agents-line` finding is reported, and the counts are checked at the cited sha
- **Test:** `tests/test_pr_hygiene.py::test_a_pr_body_whose_agents_sha_is_an_older_main_passes`

#### Scenario: counts that do not match that sha's AGENTS.md are rejected

- **Given** a PR body whose `AGENTS:` sha is right and whose byte count is not
- **When** `check-pr-hygiene` reads it
- **Then** it reports a finding naming the field and the real value
- **Test:** `tests/test_pr_hygiene.py::test_a_pr_body_whose_agents_counts_are_wrong_is_a_violation`

#### Scenario: a human-authored PR is not held to the bot contract

- **Given** a PR whose added commits are authored by a person, not `Asimov Agent`
- **When** `check-pr-hygiene` reads its body with no `AGENTS:` line
- **Then** no `pr-agents-line` finding is reported (every other rule still applies)
- **Test:** `tests/test_pr_hygiene.py::test_a_human_authored_pr_is_not_held_to_the_agents_line`

#### Scenario: a bot range is still held to the line

- **Given** a PR whose added commits are all authored by `Asimov Agent <support@docondee.com>`
- **When** `check-pr-hygiene` reads a body with no `AGENTS:` line
- **Then** it reports the missing-line finding
- **Test:** `tests/test_pr_hygiene.py::test_a_bot_range_is_held_to_the_agents_line`

#### Scenario: the body is read from the event, not the network

- **Given** a `GITHUB_EVENT_PATH` file carrying `pull_request.body`
- **When** `check-pr-hygiene` reads the body with no `PR=`/`REPO=`
- **Then** it reads that body and makes no network call
- **Test:** `tests/test_pr_hygiene.py::test_the_pr_body_is_read_from_the_github_event_without_network`

#### Scenario: a push to main has no body to read and does not fail

- **Given** no body source at all
- **When** `check-pr-hygiene` runs
- **Then** it says it read no PR body and the static half still decides the exit code
- **Test:** `tests/test_pr_hygiene.py::test_with_no_pr_body_the_static_half_still_decides`

### Requirement: the shared unattended contract carries the preflight

`bot-unattended`, the skill every leg preloads, MUST state the preflight: fetch `main`, fast-forward
or stop, re-read `AGENTS.md`, and cite it in the artifact the leg produces.
`make check-agent-skills` MUST fail when that skill loses the rule, so a leg cannot be written that
omits it.

WHEN the shared skill is read
THEN it states the preflight, and the gate fails when the statement is gone.

#### Scenario: the unattended skill states the preflight

- **Given** `.hermes/skills/bot-unattended/SKILL.md`
- **When** `make check-agent-skills` reads it
- **Then** no `unattended-preflight` finding is reported
- **Test:** `tests/test_agent_skills.py::test_the_unattended_skill_states_the_preflight`

#### Scenario: a skill that dropped the rule fails the gate

- **Given** a fixture tree whose `bot-unattended` skill lost the preflight paragraph
- **When** `check_agent_skills.findings` reads it
- **Then** it reports `unattended-preflight`
- **Test:** `tests/test_agent_skills.py::test_a_skill_that_dropped_the_preflight_fails_the_gate`

### Requirement: the target is wired, documented and phony

`make bot-preflight` MUST exist, MUST be declared in `.PHONY:`, MUST carry a `##` help line, MUST be
named in `docs/BOTS.md`, and MUST forward `PROFILE=`, `CHECK=1`, `REMOTE=` and `BRANCH=` to the
script.

WHEN the Makefile and the docs are read
THEN the target, its help line, its `.PHONY` entry and its documentation all exist.

#### Scenario: the make target is wired, phony and documented

- **Given** the real checkout
- **When** `Makefile` and `docs/BOTS.md` are read
- **Then** `bot-preflight` is a target with a `##` help line, is in `.PHONY:`, is named in
  `docs/BOTS.md`, and its recipe forwards the four parameters
- **Test:** `tests/test_bot_preflight.py::test_the_make_target_is_phony_documented_and_forwards_the_profile`
