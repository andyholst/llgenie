# engine-skill-automation

## ADDED Requirements

### Requirement: a spawned tracking issue is queued for the bots, and the queue is proven

`make spawn-engine-skill-issues` MUST place every tracking issue it creates — and every open tracking
issue it finds that has lost the label — in the queue the implementer bot reads (`agent:implement`), by
applying the label explicitly after the create and then reading the labels back. It MUST fail the step,
naming the issue, when the label is not present after the write. `--dry` MUST mutate nothing.

WHEN the weekly sync spawns a tracking issue for an engine llgenie does not ship
THEN the issue carries `agent:implement`, verified by reading it back, and the step is red if it does not.

#### Scenario: the created issue is labelled and read back

- **Given** a registry that names an engine no skill covers, no dated decision for it, and a `gh` whose
  `issue create` silently drops `--label` (the measured CI behaviour)
- **When** `make spawn-engine-skill-issues` runs
- **Then** one issue is created for that engine
- **And** `gh issue edit <n> --add-label agent:implement` is called for it
- **And** the label is read back with `gh issue view <n> --json labels` and is present
- **Test:** `tests/test_engine_skill_gap.py::test_a_spawned_tracking_issue_lands_in_the_bots_queue`

#### Scenario: an existing unlabelled issue is repaired, not skipped

- **Given** an open tracking issue for the engine that does not carry `agent:implement`
- **When** `make spawn-engine-skill-issues` runs again
- **Then** no duplicate issue is created
- **And** the existing issue is labelled `agent:implement`
- **Test:** `tests/test_engine_skill_gap.py::test_spawn_is_idempotent_and_creates_nothing_for_a_decided_engine`

#### Scenario: a label that does not land fails the step

- **Given** a `gh` where `issue edit --add-label` has no effect
- **When** `make spawn-engine-skill-issues` runs
- **Then** the step exits non-zero and names the issue number and the missing label
- **Test:** `tests/test_engine_skill_gap.py::test_a_tracking_issue_that_cannot_be_labelled_fails_the_step_naming_it`

### Requirement: a registry engine can be scaffolded into a skill without inventing a fact

`make engine-skill-scaffold ENGINE="<registry name>"` MUST write `skills/engines/<id>/SKILL.md` carrying
the facts the registry states — engine name, upstream repo URL, `backends` derived from the registry's
`backend` string — and MUST leave every upstream fact it cannot prove empty: `description`, `ref`,
`pinned`, `verified`, `license`, `formats`, `upstream_watch`, `prereqs`, `install`, `binary`, `detect`,
`launch`, `health`, `alias_mode`. It MUST NOT overwrite an existing skill unless forced, MUST NOT
invent a backend from a wording it cannot place (it fails naming the string and the override), and MUST
refuse an engine name the registry does not list.

WHEN a registry engine has no skill
THEN the scaffold writes a skill whose registry facts are filled and whose unprovable keys are empty,
so `make skills-validate` names each one.

#### Scenario: registry facts are filled and unprovable keys are empty

- **Given** a registry entry naming an engine, its repo URL and `backend: CUDA / ROCm`
- **When** `make engine-skill-scaffold ENGINE=<that engine>` runs
- **Then** `skills/engines/<id>/SKILL.md` carries the engine name, the repo URL and
  `backends: [cuda, rocm]`
- **And** `ref`, `pinned`, `license`, `install`, `binary`, `detect`, `launch`, `health` and
  `alias_mode` are empty, and the real `engine_skills.validate()` names each of them
- **Test:** `tests/test_engine_skill_scaffold.py::test_scaffold_writes_the_registry_facts_and_leaves_every_unprovable_key_empty`

#### Scenario: an existing skill is never overwritten by a scaffold

- **Given** a skill already on disk with a pinned `ref`
- **When** the scaffold runs again, and then with force
- **Then** the first run writes nothing and reports that the skill exists
- **And** only the forced run rewrites the file
- **Test:** `tests/test_engine_skill_scaffold.py::test_scaffold_never_overwrites_a_shipped_skill_unless_forced`

#### Scenario: an unplaceable backend wording is refused

- **Given** a registry entry whose `backend` names no backend llgenie knows
- **When** the scaffold runs without an explicit backend list
- **Then** it fails loudly, quoting the registry's wording and naming `--backends`
- **Test:** `tests/test_engine_skill_scaffold.py::test_scaffold_refuses_a_backend_string_it_cannot_place`

#### Scenario: the id and the backend list follow the caller's explicit values

- **Given** a dotted upstream engine name
- **When** the scaffold runs with `--id` and `--backends`
- **Then** the skill is written under that id with exactly those backends
- **Test:** `tests/test_engine_skill_scaffold.py::test_scaffold_accepts_explicit_backends_and_slugs_a_dotted_engine_id`

#### Scenario: an engine the registry does not list is refused

- **Given** a registry that lists one engine
- **When** the scaffold is asked for a name it does not contain
- **Then** it refuses and suggests the registry's spelling
- **Test:** `tests/test_engine_skill_scaffold.py::test_scaffold_names_an_engine_the_registry_does_not_list`

#### Scenario: a preview writes nothing

- **Given** a registry engine and an empty skills directory
- **When** the scaffold runs in dry mode
- **Then** no file is written
- **Test:** `tests/test_engine_skill_scaffold.py::test_dry_writes_nothing`

### Requirement: the issue-bot scaffolds an engine tracking issue before the agent starts

`scripts/issue_implementer.py dispatch` (`make issue-bot-dispatch`, the step `issue-bot.yml` runs
before the implement leg) MUST recognize an engine tracking issue by its title, write the skill for the
engine it names, and append a `## Scaffold` section to `issue.md` naming the file, its backends and what
is still empty. It MUST NOT do this on a dry run, MUST NOT write anything for a plain issue, and MUST
report an engine the vendored store no longer names in that section instead of failing the dispatch.

WHEN the issue-bot picks up a tracking issue for an engine llgenie does not ship
THEN `skills/engines/<id>/SKILL.md` exists before the agent reads `issue.md`, and `issue.md` says so.

#### Scenario: the skill is written before the agent reads issue.md

- **Given** an `agent:implement` issue titled `engine: <name> has no llgenie skill (…)` and a registry
  naming that engine with a repo URL and `backend: CUDA / ROCm`
- **When** `make issue-bot-dispatch` runs
- **Then** `skills/engines/<id>/SKILL.md` is written with the repo URL and `backends: [cuda, rocm]`
- **And** `issue.md` carries a `## Scaffold` section naming that path, the empty keys and
  `make generate-engine-params`
- **Test:** `tests/test_issue_implementer.py::test_dispatch_scaffolds_the_skill_of_an_engine_tracking_issue`

#### Scenario: a plain issue is untouched

- **Given** an ordinary implementation issue
- **When** `make issue-bot-dispatch` runs
- **Then** no skill file is written and `issue.md` carries no `## Scaffold` section
- **Test:** `tests/test_issue_implementer.py::test_dispatch_scaffolds_nothing_for_a_plain_issue`

#### Scenario: a dry dispatch writes nothing

- **Given** an engine tracking issue
- **When** `make issue-bot-dispatch DRY=1` runs
- **Then** no skill file is written
- **Test:** `tests/test_issue_implementer.py::test_a_dry_dispatch_scaffolds_nothing`
