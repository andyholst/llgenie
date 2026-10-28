# ci-path-scope — Tasks

Issue: [#824](https://github.com/asimov-agent/llgenie/issues/824) (part a)

- [x] 1. `scripts/ci_scope.py` classifies a diff into nine classes, with ten wildcard paths selecting every class and an unmatched path exiting 1 by name.
- [x] 2. The job table matches `ci.yml` as it is today (15 jobs, Linux-only, post-#871), asserted against the workflow by test.
- [x] 3. `ci.yml` carries `pull_request.paths-ignore` = `DOCS_TRIGGER_IGNORE` (the `docs` class minus wildcards, `AGENTS.md` re-included); `push` carries no filter.
- [x] 4. `.github/workflows/scope.yml` runs with no path filter, one job `scope`, and the docs gates inside.
- [x] 5. `tests/test_ci_scope.py` covers one case per class, one per wildcard, the wildcard-beside-docs case, the unmatched CLI, the docs-only selection (<10 jobs), the engine selection, the report shape, and the two anti-drift assertions (job names vs `ci.yml`, `paths-ignore` vs the constant, `scope.yml`'s shape).
- [x] 6. `make check-workflows`, `check-wiring`, `check-docs`, `lint`, `openspec-validate`, `openspec-tasks-check` and the workflow-hygiene suite pass with no new allowlisted `if:`.
