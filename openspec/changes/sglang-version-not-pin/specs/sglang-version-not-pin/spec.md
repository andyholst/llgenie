# sglang-version-not-pin

## ADDED Requirements

### Requirement: a fallback version is a version, never a commit sha

An engine skill's `detect` MUST print a version-shaped string. When the installed distribution cannot
report one, the fallback MUST be the pinned version (the skill's `version:`, e.g. `0.5.22`), never the
commit sha.

WHEN an engine's detect has to fall back
THEN it prints the pinned version, so `make test-built-engine` accepts it.

#### Scenario: the rocm wheel reports 0.0.0

- **Given** `sglang/rocm` whose distribution metadata reports `0.0.0`
- **When** its detect runs in the published image
- **Then** it prints `sglang 0.5.22`, not `sglang pin <sha>`
- **Test:** `tests/test_engine_skills_pipefail.py::test_no_engine_reports_a_commit_sha_as_its_version`

#### Scenario: the guard covers every engine

- **Given** every skill under `skills/engines/`
- **When** the guard reads their `detect` lines
- **Then** none of them contains `{pinned_short}`
- **Test:** `tests/test_engine_skills_pipefail.py::test_no_engine_reports_a_commit_sha_as_its_version`
