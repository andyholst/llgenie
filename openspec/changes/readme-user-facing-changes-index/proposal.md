# README is the user guide; every change is a dated note indexed by CHANGES.md (issue #678)

## Why

`README.md` was 2,622 lines and 37 `##` sections, most headed `(issue #NNN)`: bot pipelines, cron
slots, secret plumbing, engine-bump internals, PR hygiene. A new user had to scroll ~1,300 lines of
change history before reaching "Download a model", and the architecture reference
(`docs/ARCHITECTURE.md`) was never linked from the top of the guide.

Three mechanisms kept feeding it:

- `AGENTS.md` ("Documentation is part of the change") told every agent and bot to mirror each change
  into `README.md`, so each landed change appended another issue-numbered section.
- `scripts/check_dispatch_forms.py` kept a generated dispatch table *inside* `README.md`, so a
  workflow edit rewrote the README.
- `scripts/engine_bump.py::_rewrite_pin_asserts` rewrote `README.md` on every engine pin.

So the README was the union of everyone's change notes. There was no stable user guide and no index
of the changes themselves.

## What changes

1. **`README.md` becomes the user document**: what llgenie is, requirements, install, use it
   (`llgenie`, the downloader, top-tier), launch/serve, layout, environment, and a short
   "how it works" with links to `docs/ARCHITECTURE.md`, `docs/ENGINES.md`, `docs/BOTS.md` and
   `CHANGES.md`. No issue-numbered change sections.
2. **`docs/BOTS.md`** takes the moved automation prose (bots, legs, secrets, redaction, merge
   policy, verification/CI, contributor rules, trigger guard, isolation) plus the generated dispatch
   table. **`docs/ENGINES.md`** takes the moved engine prose (llama.cpp build rule, tree/backend
   selection, install targets, CI matrix, engine skills, on-demand builds, container images).
3. **`CHANGES.md`** is the change index: one row per change (date, one-line change, link to its
   `agent-wiki/` note, issue/PR), newest first, linked from the README.
4. **Each change keeps its own Zettelkasten note** in `agent-wiki/YYYY-MM-DD-<kebab>.md`, referenced
   from `CHANGES.md` and from the OpenSpec change that drove it. The existing notes are indexed in
   one pass.
5. **`scripts/check_docs.py` is the gate** and now checks the whole rule: a user-facing target must
   be named in `README.md` or a `docs/` page the README links; every `agent-wiki/` note must
   reference an issue/PR and be indexed in `CHANGES.md`; every index row must point at an existing
   note; `README.md` must link `CHANGES.md`; and `README.md` must carry no issue-numbered change
   heading, no change-log heading, and no dispatch-table marker.
6. **No bot writes `README.md`**: `check_dispatch_forms.py` verifies the table in `docs/BOTS.md`,
   `engine_bump.py` rewrites `tests/` and `docs/` only, and `engine-bump.yml` stages `docs/` instead
   of `README.md`.
7. **`AGENTS.md`** is amended: the documentation rule is a dated note + `CHANGES.md` row in the same
   commit, README changes are for user-facing behaviour only, and a bot never writes the README.

## Impact

- `README.md` — rewritten as the user guide (2,622 → ~660 lines).
- `CHANGES.md` — new (the index).
- `docs/BOTS.md`, `docs/ENGINES.md` — new (the moved reference prose).
- `scripts/check_docs.py` — the documentation surface, the index checks, the README-purity checks.
- `scripts/check_dispatch_forms.py` — the table's home is `docs/BOTS.md`.
- `scripts/engine_bump.py`, `.github/workflows/engine-bump.yml` — `tests/` + `docs/`, never the README.
- `Makefile` — `check-docs` / `docs-report` / `check-dispatch-forms` help text.
- `AGENTS.md` — the "Documentation is part of the change" section.
- Tests: `tests/test_check_docs.py` (rewritten for the new contract), `tests/test_dispatch_forms.py`,
  `tests/test_issue_bot_manual_pick.py`, `tests/test_auto_merge.py`,
  `tests/test_architecture_bot.py`, `tests/test_agent_nerve.py`, `tests/test_engine_bump.py`.
