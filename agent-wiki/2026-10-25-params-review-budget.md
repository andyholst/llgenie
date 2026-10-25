# 2026-10-25 — the review brief is a selection, not the whole tree (#597)

Issue: **#597**, filed from the first real run of the leg #583 added. PR: this branch's PR against
`asimov-agent/llgenie:main`.

## What the first real run showed

`make engine-params-review-brief ENGINE=strata` on `main` with `strata` at `v0.2.4`:

```
[params-review] strata: 214 documentation file(s) at 0303f658 -> params-review-in.md
-rw-r--r-- 1 asimov asimov 1844709 params-review-in.md      # 1.8 MB, 424 sections
```

The largest sections were `bench/results/…/README.md` pages, while the root `CMakeLists.txt` — the file
that proves the flags — was cut at the 20 KB per-file cap.

## The decision

`_docs()` ranks and doubly-bounds the selection: noise trees out (`bench/`, `benchmarks/`, `examples/`,
`tests/`, `fixtures/`, `assets/`, `apps/`), flag-proving files first within their own 45 KB share (root
before nested, 60 KB per file), the rest by build vocabulary up to 80 KB, and the brief prints how many
files were omitted. `docs/*.md` is matched explicitly because `Path.match` does not let `**` cross zero
directories — `docs/BUILDING.md` had been invisible.

## Verification

- `tests/test_engine_params_review.py` — 11 pass: a real-git fixture dominated by bench pages asserts no
  bench page is selected, the total is within budget, the omitted count is reported and the CMakeLists
  keeps its LAST `option(...)` line past the prose cap; a small tree asserts `docs/BUILDING.md` is found
  and outranks prose.
- Measured on the real engine: `strata` **1 844 709 → 81 145 bytes**, 424 → 8 sections, selecting the
  root `Dockerfile`, two `CMakeLists.txt`, three Dockerfiles and `docs/AMD_HIP.md` + `docs/DETAILS.md`.
- `make test-unit`, `make openspec-validate NAME=params-review-budget`, `make lint`, `make check-docs`.

## Status

The bot never merges; CI's `auto-merge` owns landing.
