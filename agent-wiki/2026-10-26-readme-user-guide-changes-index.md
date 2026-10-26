# 2026-10-26 — the README is the user guide, changes are dated notes indexed by CHANGES.md

Implements issue #678 (OpenSpec change `readme-user-facing-changes-index`).

## What was wrong (measured before this note)

`README.md` was **2,622 lines** with **37 `##` sections**, most of them headed `(issue #NNN)` — bot
pipelines, cron slots, secret plumbing, engine-bump internals, PR hygiene. The first user-usable
instruction ("Download a model") sat at line 1,851. Three producers kept feeding it: the AGENTS.md
documentation rule told every agent to mirror each change into the README,
`scripts/check_dispatch_forms.py` kept a generated table *inside* it, and
`scripts/engine_bump.py::_rewrite_pin_asserts` rewrote it on every engine pin. Nobody owned the
file, so it was the union of everyone's notes.

## What was decided

- **One home per kind of text.** The README is the user guide (install → use → how it works).
  Automation is `docs/BOTS.md`; engines are `docs/ENGINES.md`; the code map stays
  `docs/ARCHITECTURE.md`. A change's own record is a dated note here, in `agent-wiki/`.
- **One index.** `CHANGES.md` lists every note (date, change, link, issue/PR), newest first, and the
  README links it — so history is one click from the guide and never appended to it.
- **The gate is the rule.** `scripts/check_docs.py` proves all of it: a `##` target is documented in
  the README or a `docs/` page it links; a note cites an issue/PR and is indexed; an index row
  points at a real note; the README reaches the index; and the README carries no issue-numbered
  heading, no change-log heading, no dispatch marker.
- **No bot writes the README.** The dispatch table is verified in `docs/BOTS.md`; the engine bump
  rewrites `tests/` and `docs/` only. A producer that writes the README is now a defect, not a
  convention.

## Verified against the spec (`specs/documentation-surface/spec.md`)

- the real tree: 202 user-facing targets documented across README + `docs/BOTS.md` +
  `docs/ENGINES.md` + `docs/ARCHITECTURE.md`; 183 notes, all cited and indexed; zero change-history
  headings (`tests/test_check_docs.py::test_the_real_tree_documents_every_user_facing_target`)
- each failure mode against real scratch trees: appended change section, `## Changelog`, dispatch
  marker, unindexed note, dangling index row, unlinked index, unlinked `docs/` page, stale exception
- `make check-dispatch-forms` green against `docs/BOTS.md`; the engine bump no longer touches the
  README (`tests/test_engine_bump.py::test_bump_rewrites_hardcoded_pin_asserts`)

## Status

Gates: `make test-unit` 5227 passed / 6 deselected, `make check-docs`, `make check-dispatch-forms`,
`make check-workflows`, `make check-wiring`, `make lint` and
`make openspec-validate NAME=readme-user-facing-changes-index` all exit 0.
Deferred (own issues, not folded in): a generated `docs/BOTS.md` target list, and grouping
`CHANGES.md` by release.
