# 2026-10-24 — an engine bump's derived params are reviewed against the engine's own docs (#583)

Issue: **#583** (implemented here). Separate change from **#580** (the bump's binary must answer
`-h`/`--version`), which is its own PR. PR: this branch's PR against `asimov-agent/llgenie:main`.

## What was missing

`make engine-bump` derives the build parameters structurally (`scripts/engine_params_derive.py`: CMake
options, `llama_option_depr` renames, recipe `-D` flags, toolchain pins, launch flags, dependencies).
The bump PR's CI then compiles them. So the chain proves the params **build**; it never proves they are
**right for this engine version and this arch**. A flag upstream's README or CUDA recipe now recommends,
but which the old params never had, is at best report-only (E4) and usually invisible — each bump kept
whatever the skill already had plus whatever a regex found.

## The decision

An `engine-params-review` Hermes project skill run as a leg between the bump and the PR, with the host
as the only writer:

1. `engine-params-review-brief` (deterministic) writes `params-review-in.md`: the engine's docs at its
   pinned sha — `README*`, `docs/**`, `CMakeLists.txt`, the recipe Dockerfiles — plus the params this
   repo builds with per backend.
2. `engine-params-review` (Hermes, `.hermes/skills/engine-params-review/`, preloading
   `bot-unattended`) writes `params-review.md` as
   `PROPOSE <backend> <-DFLAG> DOC <path> "<quote>" WHY <reason>` lines, or `NO REVIEW: <reason>`.
3. `engine-params-review-apply` decides. A proposal is accepted only when the backend is one the
   engine builds (or `common`), the file exists at the pin, the flag's `NAME` is in it, the **quote is a
   substring of it**, and the flag is not already present. Accepted flags are appended to
   `cmake_flags.<backend>` in the skill, `make generate-engine-params` regenerates params and
   Dockerfiles, and `params-review-section.md` lists what was applied (with its document) and every
   refusal with its reason.

Refusals are the point: the LLM cannot invent a flag, and a paraphrase is not evidence. The workflow
step is `continue-on-error` and sits before the PR step, which appends the section to the body — a review
that fails still opens the PR.

## Verification

- `tests/test_engine_params_review.py` — 9 pass in the CI test image: the documented arch flag is
  accepted and written to the CUDA line only; `DRY=1` reports and mutates nothing; an undocumented flag,
  a quote not in the file, a backend the engine does not build and a flag already present are each
  refused with their own reason; the PR section reports both sides and a silent review says so; the
  workflow step is non-fatal and ordered before the PR.
- `tests/test_bot_scratch_ignored.py` — the three run inputs are in `.gitignore` and in the roster, so no
  `git add -A` can ship them (the #427 lesson).
- `make test-unit`, `make openspec-validate NAME=engine-params-review`, `make lint`, `make check-docs`,
  `make check-wiring`, `make check-dispatch-forms`.

## Status

The bot never merges; CI's `auto-merge` owns landing.
