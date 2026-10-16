# workflow-file-valid — a workflow file GitHub refuses must fail CI, not `main`

## Why

`main` carried `.github/workflows/engine-bump-rebase.yml`, a file GitHub **refuses to parse**. Every
push to `main` that touched the workflows directory landed a red run for it that is
`completed`/`failure` with **zero jobs**, whose `name` is the file PATH rather than the workflow's
`name:`, and for which `gh run view <id> --log-failed` answers `log not found`. Measured on `main`
(newest first): `38850302335` (`ed75b870`), `38850145191` (`c9fc82c4`), `38849945773` (`38d54aa1`),
`38844778241` (`e2715093`) — four in a row, all `push`, all 0 jobs.

The cause is one line: a `#` line inside a `run: |` block is **script text, not a YAML comment**, so
its literal `${{ ... }}` is parsed as an expression — and `...` is not an expression. `yaml.safe_load`
accepts it (PyYAML has no notion of `${{ }}`), the workflow guard does not check expressions, and no
CI job opened the workflow files, so it shipped.

The cost is the signal, not the work: the daily engine-bump rebase is `schedule` + `dispatch` only, so
its failing `push` runs cost no real job — but "is `main` green?" stops being answerable, and the
next workflow that *does* matter would fail the same silent way.

## What Changes

- **The refused file is fixed.** The comment in `.github/workflows/engine-bump-rebase.yml` is reworded
  so no literal GitHub expression remains inside its `run:` block.
- **A gate validates every workflow file on every run.** New `make check-workflows`
  (`scripts/check_workflows.py`), wired into `ci-unit`, fails when a workflow is one GitHub refuses:
  - `bad-expression` — a `${{ … }}` that does not parse (the class that shipped);
  - `unterminated` — a `${{` with no closing `}}`;
  - `duplicate-key` — the same key twice in one mapping (GitHub refuses it; PyYAML keeps the last);
  - `missing-name` — no top-level `name:`, which is what makes a 0-job run present itself as a path.
- **Unit tests pin it** (`tests/test_workflows_valid.py`, wired into `make test-unit`): the guard
  fires on the exact pre-fix text, passes on this repository, every workflow parses as strict YAML
  with no duplicate keys, and the guard is wired into the repo.
- **`AGENTS.md` states the rule**, so the next agent knows a `#` inside `run:` is script text and a
  rejected file shows up as a 0-job run named after its path.

## Impact

- New: `scripts/check_workflows.py`, `tests/test_workflows_valid.py`, `make check-workflows`,
  `make workflows-report`.
- Changed: `.github/workflows/engine-bump-rebase.yml` (one comment), `Makefile` (`ci-unit`,
  `test-unit`, `.PHONY`, help), `README.md`, `AGENTS.md`.
- No behaviour change for any job that already ran: the daily rebase keeps its `schedule` + dispatch
  triggers and its `dry` branch exactly as they were.

## Not covered

- **#329** — actionlint's shellcheck findings across the other workflows (SC2086 / SC2016 / SC2129).
  GitHub ACCEPTS those files, so they are lint debt, not the refusal fixed here; filed separately so
  a reviewer sees this change ship only the refused-file fix plus its gate.
- **#318** — the same 0-job symptom, filed before the cause was isolated; it is superseded by this
  change (the cause and the fix live here).
