# agent-profiles

## ADDED Requirements

### Requirement: a live skill directory with no tree twin is one finding

`scripts/check_agent_profiles.py` MUST report a live skill directory that the tree does not mirror at
the same relative path as ONE finding with the key `absent-from-tree` (never one finding per file
inside it), naming the profile, the directory's path relative to the profile and its file count, and
`check` MUST exit 1 on it. A skill directory is a directory carrying a `SKILL.md`, at any depth under
`skills/`; a Hermes category (`skills/software-development/`) is not a skill directory and MUST NOT be
reported as one. A lane with no live profile on the host MUST NOT produce the finding (`absent-live`
is a different condition).

#### Scenario: a whole live-only skill directory is named once

- **Given** a tree profile whose `skills/` holds no skill directory
- **And** a live profile whose `skills/software-development/llgenie-lane-skill/` carries
  `SKILL.md` and `references/a.md`
- **When** the gate runs
- **Then** it reports exactly one `absent-from-tree` finding, `where` names
  `someone/skills/software-development/llgenie-lane-skill`, the detail carries `2 file(s)`, and
  `check` exits 1
- **Test:** `tests/test_agent_profiles.py::test_a_whole_live_only_skill_directory_is_one_finding_naming_lane_path_and_count`

#### Scenario: the negative control turns the gate red then green

- **Given** a tree and a live profile that agree
- **When** a whole skill directory is planted only in the live profile
- **Then** `main(["check", …])` exits 1 and prints
  `FAIL absent-from-tree: someone/skills/software-development/llgenie-lane-skill`
- **And** when the directory is removed the same call exits 0
- **Test:** `tests/test_agent_profiles.py::test_the_check_fails_naming_a_live_only_directory_and_passes_once_it_is_removed`

#### Scenario: a tree category is not a skill directory

- **Given** a tree skill at `skills/software-development/llgenie-pr-review/`
- **And** a live `skills/software-development/` carrying that skill plus the shared library
- **When** the gate runs
- **Then** neither the mirrored skill nor the library beside it is a finding
- **And** a file that exists only in the live mirrored skill IS named, with the category path in
  `where`
- **Test:** `tests/test_agent_profiles.py::test_a_tree_category_directory_is_not_a_skill`

### Requirement: only the lane's own live skills are compared

The gate MUST decide "lane behaviour" structurally, never from a name list. A live skill MUST produce
no finding when it is recorded in Hermes's own install records (`skills/.bundled_manifest` or
`skills/.hub/lock.json`), when the same skill exists in the shared library the profiles are seeded from
(`<hermes-home>/skills`, the sibling of the `profiles/` directory), or when the skill directory is a
symlink out of the profile. Bookkeeping (hidden names, `__pycache__`) MUST produce no finding either.

#### Scenario: the bundle, the hub and the shared library are not lane skills

- **Given** a live profile whose `.bundled_manifest` names `docx`, whose `.hub/lock.json` installs
  `notion`, and whose Hermes home `skills/` carries `shared-only`
- **When** the gate runs
- **Then** none of the three is a finding
- **Test:** `tests/test_agent_profiles.py::test_the_library_hermes_installs_is_not_a_lane_skill`

#### Scenario: a skill symlinked out of the profile is not a lane skill

- **Given** a live profile whose `skills/` holds a symlink to a directory outside the profile
- **When** the gate runs
- **Then** the symlink is not a finding
- **Test:** `tests/test_agent_profiles.py::test_a_skill_symlinked_out_of_the_profile_is_not_a_lane_skill`

### Requirement: without the shared library the directory comparison is skipped audibly

When the live profiles home exists but the shared library beside it does not, the gate MUST NOT report
live skill directories (it cannot tell the lane's skills from the machine's) and MUST print an audible
caveat saying the comparison did not run. A skip that cannot be seen is the defect this gate exists to
prevent.

#### Scenario: no shared library is stated, not guessed

- **Given** a live profiles home with no `skills/` directory beside it
- **And** a live-only skill directory under one of its profiles
- **When** `main(["check", …])` runs
- **Then** no `absent-from-tree` finding is reported for the directory
- **And** stderr carries `live-only skill DIRECTORIES were NOT compared`
- **Test:** `tests/test_agent_profiles.py::test_no_shared_library_means_the_directory_comparison_is_skipped_not_guessed`
