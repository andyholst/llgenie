# 2026-10-26 — the unit gate stops requiring a tag its own PR is publishing

Issue: [#672](https://github.com/asimov-agent/llgenie/issues/672)
OpenSpec: `openspec/changes/unit-gate-bump-race`
PR: [#674](https://github.com/asimov-agent/llgenie/pull/674)

## What was wrong

`make test-unit` ran `tests/test_ci_publish_order.py::test_every_image_install_pulls_is_published`,
which resolved the **current checkout's** `install` plan and asked the real GHCR whether each cpu tag
existed. On `main` that is true. On a bump PR it is false by construction: the bump changes an
engine pin, so the tag it resolves has never existed, and it is created only by the same run's
parallel `engine-image-*` job.

Measured on the open bump PRs (2026-10-26):

```
#665  [install] FAIL llama.cpp/cpu: …/llama-cpp:74b104c9-e07a7432-cpu was never published (404)
      1 failed, 5195 passed, 6 deselected in 2572.39s
#663  same test on linux AND macos (macos: 1 failed, 5195 passed in 4307.56s)
```

Both tags answered `200` minutes later, once the run had pushed them — the gate was racing its own
pipeline, not finding a defect. #169 fixed this shape for the `install` job by making
`make ci-wait-engine-images` a prerequisite of `ci-install` (30-minute budget, `install_plan` the
single tag list); the unit case kept its own copy of the assertion and never got that fix.

## What changed

`tests/test_ci_publish_order.py`:

- `_deferred_engines()` — an engine is deferred when its `containers/engines/params/<id>.json`
  differs from `origin/main` (`git show origin/main:<path>`), or has no copy there (a first import).
  No git on PATH → nothing is deferred, i.e. the previous, stricter behaviour.
- `_assert_published(deferred)` — checks the registry for every cpu image this change did **not**
  repin via `wait_published(only=[...])`, prints the deferred engines with the gate that covers
  them, and fails loudly when a checked tag is missing.
- Three cases lock it: a bump defers only its own engine and still checks the rest; a params file
  identical to the base is not deferred; a params file with no base copy is deferred.

Nothing is skipped or deleted: on `main` (deferred set empty) all cpu images are still asserted
against the real registry.

## Verified

- On a bump checkout (`chore/engine-bump-llama.cpp`, pin `master@74b104c9`) with the fixed file:
  `deferred: {'llama.cpp'}` and `10 passed` — the case that used to fail now passes.
- On this branch (params identical to `origin/main`): `deferred: set()` and `10 passed`.
- `make openspec-validate NAME=unit-gate-bump-race` green; `make test-unit` green (full suite).
