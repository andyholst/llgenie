## ADDED Requirements

### Requirement: ratchet-names-the-offending-site

`scripts/check_import_roots.py ratchet` SHALL name the `file:line` of every finding its over-counted
rule counted, in addition to the aggregate line, while keeping exit code `1` on any item and exit code
`0` when every count is at or below `tests/fixtures/import-roots-baseline.json`.

#### Scenario: a planted root reds naming that file and line

- **Given** a tree whose baseline records one `sys-path` finding, and a test file that adds a further module-level `sys.path` entry
- **When** `python3 scripts/check_import_roots.py ratchet --root <tree>` runs
- **Then** it exits 1 and its output names the offending `tests/…:line`
- **Test:** `tests/test_import_roots.py::test_the_ratchet_names_the_offending_file_and_line`

#### Scenario: no extra root keeps the command green and prints no site list

- **Given** a tree whose counts equal its recorded baseline
- **When** the ratchet runs
- **Then** it exits 0 and its output carries no `file:line` site line
- **Test:** `tests/test_import_roots.py::test_the_ratchet_is_green_and_names_no_site_when_nothing_was_added`

#### Scenario: removing a root stays green

- **Given** a tree with fewer findings than its recording
- **When** the ratchet runs
- **Then** it exits 0, because the count may only shrink
- **Test:** `tests/test_import_roots.py::test_the_ratchet_stays_green_when_a_root_is_removed`

#### Scenario: the report command is unchanged and still lists findings

- **Given** a tree with one bare `scripts/` import
- **When** `report` runs
- **Then** it prints that `tests/…:line` and exits 0
- **Test:** `tests/test_import_roots.py::test_report_still_lists_every_finding_and_exits_zero`
