# 2026-10-28 — a shipped engine that CI never builds is now red, in the right order

**Issue:** [#771](https://github.com/asimov-agent/llgenie/issues/771) · **PR:** [#776](https://github.com/asimov-agent/llgenie/pull/776) · **OpenSpec:** `engine-ci-coverage`

## What was wrong

The pipeline covered a new registry engine in stages, and every stage had a gate except the one that
proves the engine is BUILT:

| step | gate | what it proved |
|---|---|---|
| registry names the engine | `check-engine-skill-gap` | a skill exists, or a dated decision in `data/unsupported-engines.json` |
| skill shaped correctly | `skills-validate` | required keys, `servable` shape, a container spec for a linux server |
| params generated | `check-engine-params` | committed params/Dockerfiles match the skill byte-for-byte |
| **the matrix builds it** | **nothing** | **—** |

`scripts/engine_image.py matrix` only emits a cell when its variant is in `CI_VARIANTS`
(`cpu, cuda, rocm, vulkan`) and not in `DISABLED`. So a shipped engine whose only cell is disabled,
whose variants name no CI variant, or whose `os` omits `linux` was green in every gate, absent from
the matrix, never pulled by `make install`, and never offered by `rank_engines`.

Measured on `main` (`7937398`): `make engine-skill-gap` → `shipped 16 (4 with no image)`;
`exllamav3-rocm` is `servable: true`, `os: [linux]`, `backends: [rocm]`, and its single `rocm` cell
is in `DISABLED` (`#103 cuda_shim needs torch >= 2.13 ROCm headers`).

## What changed

- `scripts/engine_coverage.py` (new): `census()` gives every shipped skill one verdict —
  `built` (a params variant in `CI_VARIANTS` that `DISABLED` does not drop), `not-an-image`
  (`servable: false`, `servable: via`, no `linux` in `os`), or `unbuilt`. `findings()` fails an
  `unbuilt` engine with no exception and a STALE `KNOWN_UNBUILT` entry whose engine is now built (or
  whose skill is gone). `KNOWN_UNBUILT` carries today's gap: `exllamav3-rocm` → `#103`.
- `Makefile`: `check-engine-coverage` + `engine-coverage-report`, both `.PHONY`. `ci-unit` runs the
  gate **after `check-engine-params`** (it reads what that step just validated) and **before
  `check-engine-source`** (which judges the same cells' install steps).
- `scripts/issue_bot_gates.py`: `check-engine-coverage` is classified in `DEFERRED` with its reason —
  every `ci-unit` gate must be classified there or `test-unit` reds (measured: the first full run failed
  `test_issue_bot_gates.py::test_the_real_tree_is_wired` naming the unclassified gate). `FAST_GATES` is
  the fixed #475 six, and widening it is that issue's follow-up, so the gate is not re-run by the bot.
- `tests/test_engine_coverage.py`: 7 cases — a dropped cell, a non-CI variant, one buildable cell,
  the three deliberately-imageless shapes, a new gap named, a stale exception, and the real tree green.
- `docs/ENGINES.md`: the ordered 5-step flow for a new engine (registry → skill → params → coverage →
  build/test/publish), so "what does what, in what order" is written where an implementer looks.
  `README.md` carries the two target lines.

## Decisions

- **The exception lives in code, not a data file.** `KNOWN_UNBUILT` follows the
  `DISABLED`/`KNOWN_NOT_SOURCE` pattern already in this repo: the reason and the tracking issue sit
  beside the rule, and a stale entry fails.
- **`via` and `servable: false` are not gaps.** `dflash2` and `mlx-fast-bonsai2` ride another
  engine's server; `webllm` is a browser runtime. Demanding an image for them would be wrong, so the
  verdict has an explicit `not-an-image` state with its own reason rather than silence.
- **`exllamav3-rocm` stays disabled.** Re-enabling the cell is `#103`'s work; this change only makes
  its invisibility loud.

## Status

`make check-engine-coverage` exits 0 on the committed tree and prints `exllamav3-rocm` as the one
recorded gap; `python3 -m pytest tests/test_engine_coverage.py -q` → 7 passed. Gates run in the
worktree: `make lint`, `make check-wiring`, `make check-docs`, `make openspec-validate`.
