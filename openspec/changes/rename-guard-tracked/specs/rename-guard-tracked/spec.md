# rename-guard-tracked

## ADDED Requirements

### Requirement: the rename guard reads only live (non-ignored) files

The old-module-name guard MUST NOT judge a file the checkout's `.gitignore` excludes, and MUST judge
every file it does not exclude.

WHEN a gitignored working file names the old module
THEN it is not a finding, locally or in CI.

#### Scenario: a bot's gitignored artifact is not a finding

- **Given** a `refine-in.md` in the checkout naming `llama_serve`
- **When** the guard reads the repo
- **Then** the file is neither read nor reported
- **Test:** `tests/test_rename_llgenie_serve.py::test_a_gitignored_file_naming_the_old_module_does_not_redden_the_guard`

#### Scenario: a tracked file that names the old module is still a finding

- **Given** the tracked tree
- **When** the guard reads it
- **Then** any tracked file naming the old module is reported
- **Test:** `tests/test_rename_llgenie_serve.py::test_no_live_file_mentions_the_old_module_name`
