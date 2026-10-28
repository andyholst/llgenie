# engine-ci-coverage — proposal

Issue: [#771](https://github.com/asimov-agent/llgenie/issues/771)

## Why

The pipeline covers a registry engine in stages, and each stage has a gate — except the one that
proves the engine is actually built:

1. `registry-sync` vendors `data/models.json`; `make check-engine-skill-gap` (ci-unit) refuses an
   engine with no skill and no dated decision.
2. `make skills-validate` (ci-unit) refuses a servable engine whose container spec is absent.
3. `make check-engine-params` (ci-unit) refuses a committed params cell / Dockerfile that drifted
   from the skill.
4. `scripts/engine_image.py matrix` builds `list-engine-images CI=1` from the params — and here the
   chain silently ends for some engines.

Nothing states that a params cell is one the matrix will BUILD. `engine_image.DISABLED` drops a cell
(`#103`), a variant outside `CI_VARIANTS` (`cpu, cuda, rocm, vulkan`) is never a CI cell, and an
engine whose `os` omits `linux` never gets an image. Measured on `main` (`7937398`):
`make engine-skill-gap` reports `shipped 16 (4 with no image)`; `exllamav3-rocm` is `servable: true`,
`os: [linux]`, and its only cell (`rocm`) is in `DISABLED` — so it is green in every gate, absent from
the matrix, never pulled by `make install`, and never offered by `rank_engines`.

## What Changes

- **`scripts/engine_coverage.py`** (new): `census()` reads the skills tree and the committed params
  and gives each shipped skill one verdict — `built` (a params variant in `CI_VARIANTS` that
  `DISABLED` does not drop), `not-an-image` (`servable: false`, `servable: via`, or no `linux` in
  `os`), or `unbuilt` (servable on linux with no buildable cell). `findings()` fails on an `unbuilt`
  engine with no recorded exception, and on a STALE `KNOWN_UNBUILT` entry whose engine is now built
  or gone. `KNOWN_UNBUILT` carries today's gap (`exllamav3-rocm`, `#103`) with its reason.
- **`Makefile`**: `check-engine-coverage` (the gate) and `engine-coverage-report` (the census), both
  `.PHONY`; `ci-unit` runs the gate immediately after `check-engine-params` and before
  `check-engine-source`, so it judges the committed params the matrix will read.
- **`tests/test_engine_coverage.py`** (new): the verdict rule (a dropped cell, a non-CI variant, one
  buildable cell, the three deliberately-imageless shapes), the exception lifecycle (a new gap fails
  naming the engine; a stale exception fails), and the real tree is green.
- No behaviour change to the build itself: the gate only refuses a silent gap.

## Impact

- Affected specs: `engine-ci-coverage` (new capability).
- Affected code: `scripts/engine_coverage.py`, `Makefile`, `tests/test_engine_coverage.py`, docs.
- Not affected: `DISABLED` (an engine stays disabled; it now just cannot be forgotten), the matrix
  (`engine_image.matrix` is untouched), `make install` and the published-image tests.

## Out of scope

- Re-enabling the disabled `exllamav3-rocm` rocm cell — that is `#103`.
- A scaffolded skill that claims `os: [linux]` for a macOS-only engine — filed as `#772`; this change
  makes such a cell loud, it does not correct the scaffold that can produce one.
- Any engine that is a `via` shell or `servable: false` (a drafter, a browser runtime): they are
  deliberately not images and the gate says so instead of demanding one.
