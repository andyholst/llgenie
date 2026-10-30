# agent-profiles

## ADDED Requirements

### Requirement: a live file with no tree twin is a finding

`scripts/check_agent_profiles.py` MUST compare the tree and the live profile in BOTH directions. For
every file that exists in the live profile and has no counterpart in `agents/<profile>/`, the gate
MUST emit a finding with the key `absent-from-tree` that names the profile, the path relative to the
profile directory, and the live file's size, and MUST fail (`check` exits 1). The comparison MUST
skip a lane with no live profile on the host entirely: `absent-live` is that condition and it MUST
NOT produce an `absent-from-tree` finding.

#### Scenario: a live-only reference file is named

- **Given** a tree whose planner skill carries `references/known.md`
- **And** a live planner profile whose same skill additionally carries `references/new-tonight.md`
- **When** the gate runs
- **Then** it reports exactly one `absent-from-tree` finding, `where` names
  `llgenie-planner/skills/llgenie-bot-orchestration/references/new-tonight.md`, and `check` exits 1
- **Test:** `tests/test_agent_profiles.py::test_a_live_only_reference_file_is_a_finding_naming_profile_and_path`

#### Scenario: a live-only file at a skill's root is named

- **Given** a tree skill directory that carries only `SKILL.md`
- **And** a live skill directory that carries `SKILL.md` plus `REFERENCE.md`
- **When** the gate runs
- **Then** the finding names `REFERENCE.md`, not only the `references/` subdirectory
- **Test:** `tests/test_agent_profiles.py::test_a_live_only_file_beside_the_skill_md_is_a_finding`

#### Scenario: a lane with no live profile produces no reverse finding

- **Given** a tree listing two profiles
- **And** a live profiles home holding only the first
- **When** the gate runs
- **Then** the absent lane produces no `absent-from-tree` finding at all
- **Test:** `tests/test_agent_profiles.py::test_a_lane_with_no_live_profile_produces_no_reverse_finding`

### Requirement: the reverse direction walks only the surface the tree mirrors

The reverse comparison MUST NOT report the contents of a live profile that the tree is not the source
of truth for. A live profile directory is a whole Hermes home: the profile's data (`state.db`,
`sessions/`, `memories/`, `cron/`, `logs/`, `.curator_backups/`, `worker-outboxes/`, `config.yaml`,
`.env`) and Hermes' shared/bundled skill library (which every profile carries, and whose files number
in the thousands) MUST produce no finding. Only `SOUL.md` and the files of a skill directory that the
tree also carries are compared.

#### Scenario: the profile's data is not behaviour and is not reported

- **Given** a live profile holding `state.db`, `sessions/s1.json`, `memories/m.md` and `logs/run.log`
- **When** the gate runs
- **Then** none of them is a finding
- **Test:** `tests/test_agent_profiles.py::test_the_profile_data_is_not_reported_by_the_reverse_direction`

#### Scenario: the shared skill library in every profile is not reported

- **Given** a live profile whose `skills/` also carries `productivity/docx/SKILL.md` and
  `creative/p5js/SKILL.md`, which the tree does not version
- **When** the gate runs
- **Then** neither is a finding, because no tree skill directory of that profile names them
- **Test:** `tests/test_agent_profiles.py::test_the_shared_skill_library_is_not_reported`

#### Scenario: a live skill directory the tree does carry is compared file by file

- **Given** a tree skill directory with `SKILL.md` and `references/a.md`
- **And** a live copy carrying the same two files
- **When** the gate runs
- **Then** it reports nothing, and adding one file live makes it report exactly that file
- **Test:** `tests/test_agent_profiles.py::test_a_clean_mirror_reports_nothing_and_one_added_file_does`

### Requirement: the existing findings keep their keys and counts

Adding the reverse direction MUST NOT remove, rename or change the meaning of an existing finding key.
On a host whose live profiles exist, the keys `live-longer`, `live-lines-missing`,
`live-edited-not-tree`, `skill-reference-missing`, `soul-missing`, `profile-unlisted` and the rest
MUST still be reported exactly as before, and the count of `live-longer` / `live-edited-not-tree`
findings MUST be asserted as a SUBSET of the expected ones, never as an exact list, so that versioning
more lanes (#1060) adds findings without reddening this gate's own test.

#### Scenario: the host census keeps the pre-existing keys

- **Given** the measured host at `main@ac12cae9`: 12 `live-longer` and 1 `live-edited-not-tree` finding
- **When** the gate runs after this change
- **Then** every one of those 13 findings is still reported, and the new key is additive
- **Test:** `tests/test_agent_profiles.py::test_the_reverse_direction_is_additive_to_the_existing_findings`

### Requirement: the reverse direction is audible in both entry points

`check` MUST print one `FAIL absent-from-tree: …` line per finding and exit 1, and `report` MUST list
the same findings under its finding count, so a reader of either entry point sees the unversioned file.

#### Scenario: report lists the reverse findings

- **Given** one live-only file
- **When** `report` runs
- **Then** the rendered text names the path and the finding count includes it
- **Test:** `tests/test_agent_profiles.py::test_report_lists_the_absent_from_tree_finding`
