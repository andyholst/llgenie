# workflow-file-valid — a workflow file GitHub refuses fails CI, not main (issue #330)

Implements **#330**. Supersedes **#318** (the same 0-job symptom, filed before the cause was
isolated). Deferred to its own issue: **#329** (actionlint's shellcheck findings).

## The finding

`main` carried `.github/workflows/engine-bump-rebase.yml`, a file GitHub **refuses to parse**. Every
workflow-touching push to `main` landed a red run for it with **zero jobs**, whose `name` is the file
PATH rather than the workflow's `name:`, and for which `gh run view <id> --log-failed` answers
`log not found` — a GitHub **startup failure**.

Measured on `main` (newest first): `38850302335` (`ed75b870`), `38850145191` (`c9fc82c4`),
`38849945773` (`38d54aa1`), `38844778241` (`e2715093`) — four consecutive `push` runs, all 0 jobs.
Verified this session that the file's *scheduled* runs still succeed (3 `schedule success` in its run
history), which is what makes the failure so misleading: the workflow works, on one trigger only.

## The cause

`.github/workflows/engine-bump-rebase.yml:92`, inside the `rebase` job's `run: |` block:

```yaml
          # folded into one `${{ ... }}` so the mode this run took is readable in the log.
```

A `#` line inside a `run: |` **block scalar is script text, not a YAML comment**, so GitHub's
expression parser reads `${{ ... }}`, cannot parse `...`, and refuses the whole file. `yaml.safe_load`
accepts it — PyYAML has no notion of `${{ }}` — so nothing in review caught it.

Verified in the run history: run `38850302335` keys `name` == `.github/workflows/engine-bump-rebase.yml`
(the path, not the `name:`), `status=completed`, `conclusion=failure`, `jobs` total_count 0.

## The fix

- The comment is reworded: no literal `${{ … }}` remains, and it now says *why* (a comment inside
  `run: |` is script text).
- New `scripts/check_workflows.py` + `make check-workflows` (in `ci-unit`), failing on
  `bad-expression`, `unterminated`, `duplicate-key`, `missing-name`; `make workflows-report` lists
  every file. The expression rule is a **tokeniser** over GitHub's expression grammar, not a `${{`
  grep, so a real expression inside a `run:` block still passes.
- `tests/test_workflows_valid.py` (in `test-unit`) pins all of it.
- README documents both targets and the rule; AGENTS.md carries the durable rule.

## Verification (real output)

- Guard fires on the **pre-fix text**: `git show origin/main:.github/workflows/engine-bump-rebase.yml`
  into a scratch tree → `[check-workflows] 1 violation(s): …:92: bad-expression — `${{...…}}` does not
  parse (unexpected '.')`.
- Guard clean on the fixed tree: `OK: 13 workflow file(s) parse`.
- Rule 6c: `tests/test_workflows_valid.py` on a pre-fix worktree (`origin/main` + the new script and
  test) → **3 failed, 7 passed**; on this branch → **10 passed**.
- To be confirmed on merge: the next workflow-touching push to `main` produces no 0-job run for
  `engine-bump-rebase.yml` (`gh run list --workflow engine-bump-rebase.yml --branch main`).

## Status

Branch `fix/workflow-file-valid`, PR against `asimov-agent/llgenie:main`. Gates: `make lint`,
`make check-workflows`, `make openspec-validate NAME=workflow-file-valid`, `make check-wiring`,
`make check-docs`; the rest of the loop runs in CI.
