# bot-preflight

## ADDED Requirements

### Requirement: a leg proves its tree is current before it reads the issue

`make bot-preflight` MUST fetch `origin/main`, MUST bring a clean checkout that is behind it forward with
`git merge --ff-only`, and MUST NOT rebase. A checkout that is dirty, or that has commits on both sides, MUST
be refused with a non-zero exit naming the paths or the ahead/behind counts — never a warning that lets the
run continue on a stale tree, and never a rewrite of the leg's own commit.

The measurement is `git merge-base --is-ancestor`, not a comparison of branch names.

#### Scenario: a clean checkout behind main is fast-forwarded

- **Given** a checkout whose `HEAD` is an ancestor of `origin/main` and a working tree with no changes
- **When** `make bot-preflight` runs
- **Then** the checkout is fast-forwarded to `origin/main` and the target exits 0

#### Scenario: a dirty checkout is refused with its paths

- **Given** a checkout behind `origin/main` with an uncommitted file
- **When** `make bot-preflight` runs
- **Then** it exits non-zero, names that file, and leaves `HEAD` where it was

#### Scenario: a diverged checkout keeps the leg's commit

- **Given** a checkout with one commit `origin/main` does not have, and one commit it lacks
- **When** `make bot-preflight` runs
- **Then** it exits non-zero reporting both counts, and `HEAD` still points at the leg's own commit

### Requirement: the rulebook is recorded, not assumed

The preflight MUST write `preflight.txt` containing the `origin/main` commit, the byte size, line count and
heading count of `AGENTS.md` **at that commit**, a sha256 digest over its `## ` and `### ` heading list, and
the line `AGENTS: <sha> <bytes>b <lines>l` that a bot PR body carries.

The digest MUST be stable across edits to a rule's prose and MUST change when a heading is added or removed,
so a reviewer can tell a wording change from a contract change.

`make bot-preflight CHECK=1` MUST re-derive the record and exit non-zero when the file on disk disagrees with
the tree it sits in.

#### Scenario: the digest separates wording from contract

- **Given** a rulebook whose body text is edited without touching a heading
- **When** the digest is recomputed
- **Then** it is unchanged — and adding a `## ` heading changes it

#### Scenario: a stale record is a failure

- **Given** a `preflight.txt` whose recorded figures do not match the tree
- **When** `make bot-preflight CHECK=1` runs
- **Then** it exits non-zero naming the stale field

### Requirement: the obligation cannot be dropped from a leg's skill

`.hermes/skills/bot-unattended/SKILL.md` MUST state the preflight, and `make check-agent-skills` MUST fail
when that obligation disappears.

#### Scenario: a leg skill that lost the preflight is refused

- **Given** `bot-unattended`'s SKILL.md with its preflight section removed
- **When** `make check-agent-skills` runs
- **Then** it exits non-zero naming the missing obligation
