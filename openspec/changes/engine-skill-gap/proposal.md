# engine-skill-gap — proposal

Issue: [#229](https://github.com/asimov-agent/llgenie/issues/229)

## Why

`registry-sync` copies **every** engine upstream lists. An engine with no
`skills/engines/<id>/SKILL.md` has no params file and no image, so `rank_engines`
drops it and a model served only by it **silently leaves the trend offer**. Today
that gap is tolerated by one loosened global flag (`ALLOW_UNSKILLED=1`): a log
line is the only signal, nothing opens a work item, and "llgenie does not ship
this engine" is indistinguishable from "nobody looked".

Measured on the 2026-10-13 registry: 24 registry engines, 16 skills, 8 unshipped
(7 of them already listed in #229, plus `Project Maya`, which arrived in the last
sync with **no** signal). Zero models are served *only* by an unshipped engine
today, but nothing would have told us if one had been.

## What Changes

- **`data/unsupported-engines.json`** — the explicit, dated, reasoned record of
  every registry engine llgenie deliberately does not ship
  (`decision`: `not-shipped` | `deferred`, `decided`, `reason`, `issue`). A gap
  that is recorded is a decision; a gap that is not recorded is not.
- **`scripts/engine_skill_gap.py`** — the gap as one computation:
  - `report` — shipped / known-unsupported / **new and unresolved**, the models
    whose only engines are unskilled (they can never be offered), the models that
    merely also list one, and the **per-engine list** (status, image variants,
    the models that list each engine, and the models it is the top-ranked engine
    for per arch — the inverse of the trend matrix);
  - `render` — writes the committed `data/engine-skill-gap.json`;
  - `check` — the gate: fails naming every unresolved engine, every stale
    decision (an engine that now ships a skill, or that upstream dropped), and a
    rendered file that is stale;
  - `spawn` — opens (or finds) **one tracking issue per unresolved engine**, so
    a new engine from a sync becomes a visible, linkable work item instead of a
    log line. Idempotent; a refused `gh` fails loudly.
- **`engine_skills.validate(..., unsupported=...)`** replaces the global
  `--allow-unskilled` flag: known decisions are tolerated per engine, an engine
  with no skill and no decision is an error that names it (issue #229, option 2).
  `make skills-validate UNSUPPORTED=data/unsupported-engines.json` and
  `make check-engine-skill-gap` run in `ci-unit`; the pinned fixture stays strict.
- **The weekly sync regenerates the engine view with the trending list**:
  `make render-engine-skill-gap` runs next to `make render-trend-list-matrix`,
  `data/engine-skill-gap.json` is committed with the registry, the sync PR body
  carries the gap markdown, and `make spawn-engine-skill-issues` opens a tracking
  issue per new engine. The job itself stays green (the sync must keep carrying
  the data, #219); the loud gate is `ci-unit`, which this PR then fails until the
  engine ships a skill or its decision is recorded.

## Not covered

- Populating a new engine's skill + params + image end to end (the work the
  spawned issue describes). That stays its own change, per #219.
- The `(arch, vram, ram)` grid's own coverage gaps: [#228](https://github.com/asimov-agent/llgenie/issues/228).
- The ranking rule itself: [#225](https://github.com/asimov-agent/llgenie/issues/225).
