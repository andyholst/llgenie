---
name: engine-params-review
description: Use when an engine-bump run must review the derived build parameters against the engine's own documentation at its new pin, and propose only parameters that documentation proves.
version: 1.0.0
author: Asimov Agent
license: CC-BY-4.0
metadata:
  hermes:
    tags: [llgenie, engine-bump, build-params, review]
---

# Engine build-parameter documentation review

`make engine-bump` moved an engine's pin and re-derived its build parameters structurally: CMake
options, renames, recipe `-D` flags, toolchain pins. That proves the params **build**. It cannot prove
they are **right for this engine version and this arch** — a flag the upstream's own docs now
recommend, but which the old params never had, is invisible to a regex.

You are the judgement step. The host stays the writer.

## Inputs

- `params-review-in.md` at the repo root: the engine's upstream documentation **at its pinned sha**
  (README, `docs/`, the backend recipe Dockerfile, `CMakeLists.txt`) and the parameters this repo
  currently builds with, per backend.
- `skills/engines/<id>/SKILL.md`: the current parameters, in `cmake_flags` / `hw_flags` / `binary_flags`.

## Output

`params-review.md` at the repo root, and nothing else:

- one line per parameter the documentation requires, recommends, or marks per-arch, and which the
  current parameters do not carry:

  ```
  PROPOSE <backend> <-DFLAG or -DFLAG=value> DOC <repo-relative path> "<quote copied from that file>" WHY <reason>
  ```

- or, when the documentation proves nothing you can quote:

  ```
  NO REVIEW: <why nothing is provable>
  ```

## Rules

- **You cannot invent a flag.** A proposal is applied only when BOTH the flag and the quoted evidence
  appear verbatim in the named upstream file at this pin. The host checks that and **drops** anything
  else, reporting it in the PR body as "proposed but not applied".
- **Quote, don't paraphrase.** The quote is checked by substring; a summary of what the docs "say" is
  a drop, not a subtle paraphrase.
- **Only `-D` flags, only this engine's backends** (`cuda`, `rocm`, `vulkan`, `cpu`, `metal`) or
  `common`. Launch flags, toolchain pins and dependency changes are not yours to propose.
- **A flag already in the params is not a proposal.** Say nothing about it.
- **Reporting nothing is a correct answer.** `NO REVIEW:` with a reason is better than a guess, and
  the PR then carries "no documentation-sourced parameter was proposed".
- **Never edit the skill, the params, the Dockerfiles, or any other file.** You write
  `params-review.md`; the host validates and applies it, then regenerates.
- **Unattended.** This run has no user: never ask a question and never wait for input. If a decision
  is genuinely open, propose nothing and say why in `NO REVIEW:`.
