# The review brief is a selection, not the whole tree

## Why

`make engine-params-review-brief ENGINE=<id>` (issue #583) bounded each file but never the total, so the
leg it feeds was handed an unusable input on a real engine. Measured on `main` (`5ac1dcf`) with `strata`
pinned at `v0.2.4`:

```
[params-review] strata: 214 documentation file(s) at 0303f658 -> params-review-in.md
-rw-r--r-- 1 asimov asimov 1844709 params-review-in.md      # 1.8 MB, 424 sections
```

The biggest sections were benchmark result pages
(`bench/results/2026-10-01-community-rtx-5090-5950x/README.md`, 20 071 bytes) while the file that
actually proves the flags — the root `CMakeLists.txt` — was cut at the 20 KB per-file cap, at a size
where its later `option(...)` lines had already gone.

Two failures in one: the leg would spend its context on bench logs, and the authoritative build file was
the least useful one in the brief.

## What changes

`_docs()` becomes a ranked, doubly-bounded selection:

- **noise trees first out** — `bench/`, `benchmarks/`, `examples/`, `tests/`, `fixtures/`, `assets/`,
  `apps/` never enter, and the noise rule wins over the always-include rule (a Dockerfile under
  `bench/results/…` is a bench artefact);
- **flag-proving files get a share, not the lot** — root `CMakeLists.txt` / `Dockerfile*` and
  `docker/**/Dockerfile*` are taken first, root before nested, each up to `ALWAYS_BUDGET` (60 KB) and all
  together up to `ALWAYS_TOTAL_BUDGET` (45 KB). Their per-file cap alone once let six such files consume
  every byte and starve the documentation;
- **the rest by build relevance** — scored on the vocabulary of building an engine (`option(`, `-D`,
  `CMAKE_`, `CUDA_ARCHITECTURES`, `GPU_TARGETS`, `cmake`, `cuda`, `rocm`, `hip`, `torch`, `pip install`,
  `apt-get`, `build`, `install`, `compile`), highest first, until `DOC_TOTAL_BUDGET` (80 KB);
- **`docs/*.md` is matched explicitly** — `Path.match` does not let `**` cross zero directories, so
  `docs/BUILDING.md`, the page that documents the flags, was invisible to a `docs/**/*.md`-only glob;
- the brief says what it did: `N file(s) selected by build relevance; M omitted for the 80 KB budget.

## Impact

- `scripts/engine_params_review.py` — `DOC_TOTAL_BUDGET`, `ALWAYS_BUDGET`, `ALWAYS_TOTAL_BUDGET`,
  `ALWAYS_INCLUDE`, `NOISE_PREFIXES`, `BUILD_SIGNALS`, `_score()`, `_is_noise()`, and `_docs()` returning
  `(docs, omitted)`; `brief()` prints the selection line, `apply` ignores the count.
- `tests/test_engine_params_review.py` — a real git fixture dominated by bench pages and prose asserts the
  CMakeLists survives past the per-file cap, the total is within budget, the omitted count is reported;
  a small-tree case asserts `docs/BUILDING.md` is found and outranks prose.
- `README.md`, `agent-wiki/` — what the brief selects.

Measured after: `strata` 1 844 709 → **81 145 bytes**, 424 → 8 sections, with the root `Dockerfile`, two
CMakeLists, three Dockerfiles and `docs/AMD_HIP.md` + `docs/DETAILS.md` — the arch/build evidence the
review is for.

Not in this change: engines whose skill carries no `cmake_flags` (strata builds through a Python
`setup.cmake_build(...)` call), for which the review is report-only by construction — filed separately.
