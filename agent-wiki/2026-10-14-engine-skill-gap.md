# 2026-10-14 — the unskilled-engine gap (issue #229)

## What was verified against the spec

- `data/unsupported-engines.json` records every registry engine llgenie ships no
  skill for, with `decision` (`not-shipped` | `deferred`), `decided`, `reason` and
  `issue`. 8 recorded (the 7 #229 named, plus `Project Maya`, which the
  2026-10-13 sync added with no signal at all — the case the gate exists for).
- `scripts/engine_skill_gap.py` computes one gap: shipped / known-unsupported /
  **new-and-unresolved**, the models no engine can offer, the models that merely
  also list an unskilled engine, and the **per-engine list** (`engines{}`: status,
  image variants, the models that list it, and the models each engine is the
  top-ranked engine for per arch — the inverse of the trend matrix, #228's
  question answered as a committed, regenerated artifact).
- `make check-engine-skill-gap` is the gate: an unresolved engine, a stale
  decision (the engine ships a skill now, or upstream dropped it) or a stale
  rendered file all fail it, naming the engine.
- `make spawn-engine-skill-issues` opens one issue per unresolved engine, with the
  upstream url, the backend, the registry note, the models affected and the two
  acceptable resolutions; idempotent (an open tracking issue is reported, never
  duplicated) and loud when `gh` refuses.
- The weekly `registry-sync` renders the gap next to the trend list, commits
  `data/engine-skill-gap.json`, reports it, and spawns the issues with
  `secrets.BUMP_TOKEN` (`issues: write`). The job itself stays green — the sync
  must keep carrying the data (#219) — and the loud gate is `ci-unit` on the PR.
- `engine_skills.validate(..., unsupported=<decisions>)` replaces the global
  `--allow-unskilled` flag: per-engine dated decisions are tolerated, an engine
  with no skill and no decision is an error that names it. `ci-unit` validates
  `data/models.json` against the decisions file and runs the gate; the pinned
  fixture stays strict.

## Measurements on the 2026-10-13 registry

24 registry engines, 16 skills, 8 unshipped (all decided, 0 unresolved today).
16 shipped skills, of which 4 ship **no image**: `DFlash2` and
`MLX-fast (Bonsai 2)` are `servable: via` drafters, `WebLLM` is
`servable: false` (a browser library), and `ExLlamaV3 (ROCm fork)` has its only
variant disabled (#103). `rank_engines` drops all four exactly like an engine with
no skill, so the report counts them as "no image" rather than "shipped and fine" —
the honest view.
0 models are served only by engines with no image; 4 models also list one
(`qwen3.8-27b`, `qwen3.8-flash-next-125b`, `glm-5.3-flash`, `qwen3.6-35b-a3b`),
each reported by name.

## Decisions worth recording

- **Known vs new.** The manifest is the decision; it is never auto-updated by the
  sync. A new engine therefore *cannot* excuse itself, and the tracking issue is
  what a reviewer resolves (ship the skill, or record the dated decision).
- **The gate's exit code is the agreement, not "today is clean".** The unit test
  asserts `check` exits non-zero exactly when the gap has unresolved engines, and
  names them — so a sync that carries a new engine keeps its artifacts, while the
  PR's `ci-unit` goes red until someone decides. That is #229's option 2
  ("fail loudly per-engine") without #223's failure mode (a red sync gate that
  stops the data from flowing).
- **Actual per-engine reasons.** Each was read from the upstream repository's own
  README/releases, which corrected three first-pass guesses:
  - `mlx-serve` is **not** Metal-only (it also ships linux CUDA tarballs) — it is
    deferred because it is shipped as native binaries with no container image and is an
    all-in-one app overlapping the `mlx` engine;
  - `omlx-exl3` is **not a server at all** — it is a one-commit patch set that adds EXL3
    format support to `oMLX` and rides oMLX's server;
  - `glm-flash-lite` **does** publish a container (ghcr.io/sybil-solutions/glm53-flash-offload)
    — it is deferred as a single-model offload engine built on SGLang + ExLlamaV3, both
    already shipped, not for a missing release.
  - `MegaCapybara` is closed-source binaries behind a launcher (no source to build from);
    `ExLlamaV3` upstream is a library whose API server is external (TabbyAPI);
    `Project Maya` is a single-model engine on top of Strata, native installer, no image;
    `llama.cpp (LlamAmpere fork)` is `not-shipped` (Ampere-only fork, a third llama.cpp
    fork to maintain).

## Can the engine list be generated without an LLM? (question from the user)

Yes, and it is today:

- `make generate-engine-params` (skills → `containers/engines/params/*.json` +
  one Dockerfile per engine × variant) is deterministic; `make build-engine`
  reads only those frozen files ("no LLM, no skill reading").
- `make engine-derive` / `make engine-bump` read the upstream tree/refs
  (`git ls-remote`, `git show`) deterministically.
- `make render-trend-list-matrix` and the new `make render-engine-skill-gap` are
  pure functions of `data/models.json` + the skills + the decisions.
- Upstream (`trending-local-llms`) registers new engines deterministically too:
  `scripts/engine_registry.py:classify_repo()` decides from the GitHub repo's
  description/topics/name whether a `engine_repo` recorded by the search agent is
  an engine (the "Auto-registered from <post>" notes in the registry).

What is **not** generated today is a brand-new engine's **skill**: nothing in
llgenie scaffolds `skills/engines/<id>/SKILL.md` (grep: no scaffold/create-skill
path; `engine_bump` requires an existing skill and only moves its pin). That is
the one step a Hermes agent bot would add, and it is the exact work the spawned
tracking issue describes. Upstream already runs that pattern: `refresh-bot.yml`
builds a Docker image with the Hermes CLI (`NOUS_API_KEY`/`FIRECRAWL_API_KEY`)
and `fix-bot.yml` + `scripts/fix_loop.sh` let Hermes repair a red PR. If we want
the same for llgenie, the missing piece is a `workflow_dispatch` job that runs
Hermes against one spawned engine issue, and it is a separate change (#229's
`Not covered`).

## Status

OpenSpec change `engine-skill-gap`, branch `feat/registry-unsupported-engines`,
PR against `asimov-agent/llgenie` (issue #229).
