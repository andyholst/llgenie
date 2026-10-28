# agent-profiles-in-repo

## ADDED Requirements

### Requirement: a host agent's behaviour lives in this repository
Every profile listed in `agents/manifest.json` MUST carry `agents/<profile>/SOUL.md`, and every skill it
carries MUST live at `agents/<profile>/skills/<name>/SKILL.md`.

WHEN a profile is listed in the manifest
THEN `agents/<profile>/SOUL.md` exists
AND `make check-agent-profiles` exits 0 for the tree.

#### Scenario: a listed profile with no directory is refused
- **Given** a manifest that lists `ghost` with no `agents/ghost/`
- **When** the gate runs
- **Then** it names `agents/ghost/ does not exist` and exits non-zero
- **Test:** `tests/test_agent_profiles.py::test_a_listed_profile_with_no_directory_fails`

#### Scenario: a profile with no SOUL.md is refused
- **Given** `agents/p1/` with no `SOUL.md`
- **When** the gate runs
- **Then** it reports `SOUL.md is missing`
- **Test:** `tests/test_agent_profiles.py::test_a_profile_without_a_soul_fails`

### Requirement: the standing rules cannot silently disappear
A `SOUL.md` MUST still state that the agent never merges without the owner's approval.

WHEN a `SOUL.md` drops the never-merge rule
THEN `make check-agent-profiles` exits non-zero naming that file.

#### Scenario: a SOUL with the rule removed fails the gate
- **Given** a `SOUL.md` whose only content is "Be helpful."
- **When** the gate runs
- **Then** it reports that the never-merge rule is gone
- **Test:** `tests/test_agent_profiles.py::test_a_soul_that_drops_the_never_merge_rule_fails`

### Requirement: a committed profile is loadable and carries no secret
A skill's frontmatter `name:` MUST equal its directory name (Hermes loads a skill by name), and no
profile file MAY contain a secret-shaped value.

WHEN a skill's `name:` disagrees with its directory, or a profile carries a token-shaped string
THEN the gate exits non-zero naming the file and the reason.

#### Scenario: a mismatched skill name is refused
- **Given** `skills/right-name/SKILL.md` declaring `name: other-name`
- **When** the gate runs
- **Then** it reports the mismatch
- **Test:** `tests/test_agent_profiles.py::test_a_skill_whose_name_disagrees_with_its_directory_fails`

#### Scenario: a token in a skill is refused
- **Given** a skill containing an `hf_…` token
- **When** the gate runs
- **Then** it reports a secret-shaped value
- **Test:** `tests/test_agent_profiles.py::test_a_profile_carrying_a_secret_shaped_value_fails`

### Requirement: the repository is the source of truth for the live profile
`make sync-agent-profile PROFILE=<p>` MUST copy `agents/<p>/` into the live profile, and
`CHECK=1` MUST compare every carried file and name the first drift, while never deleting a file the
repository does not carry.

WHEN the tree and the live profile differ
THEN `CHECK=1` exits 1 naming the file
AND a plain sync rewrites it from the tree
AND a live-only file survives untouched.

#### Scenario: sync then check agree, and a live-only file survives
- **Given** a profile directory and a fake live home
- **When** `sync` runs, then a live file is edited and a live-only file is added
- **Then** `check` exits 1, a second `sync` restores the tree's text, and the live-only file is unchanged
- **Test:** `tests/test_agent_profiles.py::test_check_names_the_first_drift_and_a_live_only_file_is_never_deleted`

#### Scenario: an unknown profile is a usage error, not a silent pass
- **Given** a profile name the manifest does not list
- **When** `sync` runs
- **Then** it exits 2 naming the known profiles
- **Test:** `tests/test_agent_profiles.py::test_an_unknown_profile_is_exit_2_not_a_silent_pass`
