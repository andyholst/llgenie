# architecture-bot-rename-guard

## ADDED Requirements

### Requirement: The retired CLI module name is refused where it is written

The rename rule (the retired CLI module name may appear only in its deprecated shim, `agent-wiki/`,
`openspec/changes/` and the guard module itself) SHALL live in one place in `scripts/`, SHALL be imported
by both `make test-unit` and the architecture bot, and SHALL be applied to the regenerated
`docs/ARCHITECTURE.md` **before** anything is committed, pushed or filed. The brief the agent reads SHALL
state the rule without spelling the forbidden name.

WHEN a doc refresh would publish a document naming the retired module
THEN the publish step refuses loudly and writes nothing,
AND  the tree-wide check and the bot's check agree, because they are one function.

#### Scenario: a doc naming the retired module is refused before any write

Given a dirty doc that names the retired CLI module
When  `publish()` runs
Then  it raises naming the doc, makes no GitHub call, creates no branch and commits nothing.

- **Test:** `tests/test_architecture_bot.py::test_publish_refuses_a_doc_that_names_the_retired_module`

#### Scenario: the brief states the rule

Given a real tree
When  the brief is derived
Then  it tells the agent the retired module must not be named, and the brief itself names it nowhere.

- **Test:** `tests/test_architecture_bot.py::test_the_brief_states_the_rename_rule`

#### Scenario: one rule reads a text

Given a line naming the retired module
When  the shared rule reads it
Then  it is reported, and the current module name is not.

- **Test:** `tests/test_rename_llgenie_serve.py::test_the_shared_rule_reads_one_text`

#### Scenario: the shim and the dated history are allowed

Given a tree whose shim, `agent-wiki/` entry and live doc all name the retired module
When  the tree is checked
Then  only the live doc is reported.

- **Test:** `tests/test_rename_llgenie_serve.py::test_the_shared_rule_allows_the_shim_and_the_dated_history`

#### Scenario: the tree stays clean

Given this repository
When  the tree-wide check runs
Then  no live file names the retired module.

- **Test:** `tests/test_rename_llgenie_serve.py::test_no_live_file_mentions_the_old_module_name`
