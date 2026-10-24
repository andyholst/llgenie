# Review the derived build params against the engine's own docs

## Why

`make engine-bump ENGINE=<id>` pins an engine to its newest upstream commit and re-derives the build
parameters deterministically (`scripts/engine_params_derive.py` — "No LLM anywhere: git, regex and
file parsing only"), then regenerates `containers/engines/params/<id>.json` and the per-arch
Dockerfiles. The bump PR's CI then **compiles** that parameter list per backend.

So the chain proves the params *build*. It never proves the params are *right for this engine version
and this arch* (issue #583):

- the extractors are structural — CMake options, `llama_option_depr` renames, removed options, recipe
  `-D` flags, toolchain versions, GPU target vars, torch pins, launch flags, new dependencies. A **new
  optional flag**, a changed default, or a documented per-arch requirement that is absent from the old
  params is at best report-only (extractor E4) or invisible; nothing proposes adopting it;
- nothing reads the engine's current documentation for the arch being built: a CUDA build and a ROCm
  build of the same engine can need different flags, and the derive has no notion of "what does this
  engine's README say for sm_89 / gfx1201";
- params therefore drift minimal: each bump keeps what the skill already had plus what a regex found.
  A parameter upstream now documents stays absent across every bump, and the only signal is a human
  reading the release notes.

## What changes

A review leg between the deterministic derive and the PR, with the **host** still the only writer:

1. **`make engine-params-review-brief ENGINE=<id>`** (deterministic, `scripts/engine_params_review.py
   brief`) writes `params-review-in.md`: the engine's documentation at its pinned sha (README, `docs/`,
   the backend recipe Dockerfile, `CMakeLists.txt` — bounded per file) plus the parameters this repo
   currently builds with, per backend, and the exact answer shape.
2. **`make engine-params-review ENGINE=<id>`** runs Hermes with the new project skill
   `.hermes/skills/engine-params-review/SKILL.md` and writes `params-review.md`: one
   `PROPOSE <backend> <flag> DOC <path> "<quote>" WHY <reason>` line per parameter the documentation
   requires, recommends or marks per-arch, or `NO REVIEW: <reason>`.
3. **`make engine-params-review-apply ENGINE=<id>`** (**the verdict, not the agent**) parses those
   lines and accepts one only when ALL hold: the backend is one this engine builds (or `common`); the
   named file exists at the pin; the flag's `NAME` appears in that file; the **quoted evidence is a
   substring of that file**; and the flag is not already in the params. Accepted flags are appended to
   `skills/engines/<id>/SKILL.md`'s `cmake_flags.<backend>`, `make generate-engine-params` is re-run,
   and the PR-body `Documentation review` section lists what was applied and every proposal that was
   refused with its reason. `DRY=1` prints the decision and mutates nothing.

Uncited proposals are dropped and reported, never applied — the LLM cannot invent a flag. A review that
proposes nothing writes the section saying the derived params stand as they are, which is a correct
answer.

`.github/workflows/engine-bump.yml` runs the three steps after `make engine-bump` and before the PR is
opened, `continue-on-error`: a review that fails or proposes nothing still opens the PR, with the
outcome in the body. The three scratch files are gitignored and in the run-input roster
(`tests/test_bot_scratch_ignored.py`), so no `git add -A` can ship them.

## Impact

- `scripts/engine_params_review.py` — brief, parse, validate, apply, PR section.
- `.hermes/skills/engine-params-review/SKILL.md` — the leg's contract (inputs, output, what it may not
  do); it preloads `bot-unattended` like every other leg.
- `Makefile` — `engine-params-review-brief`, `engine-params-review` (agent leg through the redaction
  seam), `engine-params-review-apply`; all three `.PHONY`.
- `.github/workflows/engine-bump.yml` — the review step and the body section.
- `tests/test_engine_params_review.py` — the accept path, every refusal, the dry run, the section.
- `tests/test_bot_scratch_ignored.py`, `.gitignore` — the three run inputs.
- `README.md`, `agent-wiki/`.

Not in this change: replacing the deterministic derive (it stays the writer), the `-h`/`--version`
execution check (#580), and reviewing engines that were not bumped.
