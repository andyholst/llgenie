# 2026-10-26 — the rename guard reads live files, not the raw tree

Issue: [#350](https://github.com/asimov-agent/llgenie/issues/350)
OpenSpec: `openspec/changes/rename-guard-tracked`

## What was wrong

`tests/test_rename_llgenie_serve.py` walked `REPO.rglob("*")`, so `refine-in.md` — the issue-refiner's
untracked, gitignored working file — was judged as a live source file and reddened `make loop`
locally while CI stayed green.

## What changed

`scripts/module_name_guard.py` now owns the file list: `_gitignore_patterns()`, `is_ignored()` and
`live_files(root)` (the walk minus ignored paths), and `hits()` uses it. A `.gitignore` matcher rather
than `git ls-files`: the unit suite runs in the test image with the checkout mounted at `/workspace`,
where `.git` points outside the mount and `git` cannot answer — measured while writing this.

The test's own `live_files()` delegates to the guard, and a new case writes a gitignored
`refine-in.md` naming the old module and asserts it is neither read nor reported.

## Verified

- 14 passed in the test image (`llgenie/test:latest`).
- RED on the pre-change tree: 3 failed, including the new gitignored-artifact case.
