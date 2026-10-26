# 2026-10-26 — the registry sync carries a new engine instead of dying on it

Implements issue #683 (OpenSpec change `registry-sync-carries-new-engines`).

## What was wrong (measured)

The weekly `registry-sync` job had landed no PR since 2026-10-13. A dispatched run on `main`
(`aa57657`, run `40390872988`) and the scheduled run `40313722697` both stop in the checks step:

```
[skills-validate] registry engine 'LemonSeed Engine' has no skill and no dated decision ...
[skills-validate] 16 skills, registry 40 engines, 16 error(s)
make: *** [Makefile:883: skills-validate] Error 1
```

Upstream's store grew 23 → 106 models and 8 → 40 engines; the checks step runs
`make skills-validate REGISTRY=… UNSUPPORTED=…` (#319), whose contract is "every registry engine has a
skill or a dated decision". So 16 brand-new engines killed the job **before** the two steps written for
that case — `make engine-skill-gap` (report) and `make spawn-engine-skill-issues` (one tracking issue
per new engine). Deadlock: the data naming the engines never lands → their issues never open → nothing
is ever decided → the data never lands.

The first suspicion (`check-registry-keys` freezing on refined hardware labels, 47 findings) was
**wrong for the current code**: #671 (merged that morning) already keys measurements by post, and the
real new store passes it (`OK: additive only … 106 models, 81 note(s)`). The earlier failures in
`39240829581` / `38687478008` were pre-#671. The blocker today is `skills-validate`.

## What was decided

Two scopes, one contract:

- **data-carrying** (`ALLOW_NEW_ENGINES=1`, used only by `registry-sync.yml`): every shipped skill is
  still validated against the registry it is about to be read with, a recorded decision is still
  honoured, and a NEW engine is named (`NOTE: … carried`) instead of failing — the next step opens its
  tracking issue.
- **refusing** (ci-unit, unchanged): the same command without the flag reds the resulting sync PR
  until each new engine ships a skill or gets a dated decision in `data/unsupported-engines.json`.

Neither scope tolerates a skill whose engine left the registry; the flag is never passed from ci-unit.

## Verified

- Real new store, throwaway worktree: `skills-validate … ALLOW_NEW_ENGINES=1` → `0 error(s)`; the same
  command without it → `16 error(s)`, naming all 16.
- `check-registry` → `OK: additive only … 106 models, 81 note(s)`; `check-quant-catalog` OK;
  `render-trend-list-matrix` 81 cases; `render-engine-skill-gap` and `engine-skill-gap` report OK.
- Tests: the carrying vs strict scopes, the workflow's exact scope, ci-unit not passing the flag, and
  the sync still spawning one issue per new engine.
- `make test-unit` on the new store and the loop gates are recorded in `tasks.md`.

## Status

Implementation complete on `feat/registry-sync-carries-new-engines`; the end-to-end proof is a
`registry-sync` dispatch on `main` after the merge reaching the PR step.
