# rename-guard-tracked — proposal

Issue: [#350](https://github.com/asimov-agent/llgenie/issues/350)

## Why

`tests/test_rename_llgenie_serve.py` walked the whole checkout (`REPO.rglob("*")`), so a file git does
NOT track reddened the local loop while CI — a fresh checkout — stayed green:

```
E  AssertionError: the CLI module is scripts/llgenie_serve.py (#251); these files still name it
E  llama_serve: ['refine-in.md']
```

`refine-in.md` is both untracked and gitignored: the issue-refiner's working file (#352) was read as a
live source file.

## What Changes

- `scripts/module_name_guard.py` — a `live_files(root)` helper (the walk minus what the checkout's
  `.gitignore` excludes) and a minimal `is_ignored()` matcher; `hits()` uses it instead of the raw walk.
  A `.gitignore` matcher rather than `git ls-files`, because the unit suite runs in the test image with
  the checkout mounted at `/workspace`, where `.git` points outside the mount and git cannot answer.
- `tests/test_rename_llgenie_serve.py` — its `live_files()` delegates to the guard, and a case writes a
  gitignored `refine-in.md` naming the old module and asserts it is neither read nor reported.

## Benefit

The guard's verdict is the same locally and in CI: a working file a bot leaves behind cannot redden a
gate, and a tracked file that names the old module still does.
