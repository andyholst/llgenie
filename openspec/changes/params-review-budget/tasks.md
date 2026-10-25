# Tasks — params-review-budget

- [x] 1. `scripts/engine_params_review.py`: `DOC_TOTAL_BUDGET` / `ALWAYS_BUDGET` / `ALWAYS_TOTAL_BUDGET`, `ALWAYS_INCLUDE`, `NOISE_PREFIXES`, `BUILD_SIGNALS`, `_score()`, `_is_noise()`.
- [x] 2. `scripts/engine_params_review.py`: `_docs()` returns `(docs, omitted)` — noise out, flag-proving files first within their share, the rest by build relevance, total bounded.
- [x] 3. `scripts/engine_params_review.py`: `docs/*.md` / `docs/*.rst` matched explicitly (a `**` glob does not cross zero directories).
- [x] 4. `brief()` prints the selection line (`N selected …; M omitted for the 80 KB budget`).
- [x] 5. `tests/test_engine_params_review.py`: bench pages excluded, total bounded, omitted reported, the last `option(...)` survives, `docs/BUILDING.md` found and ranked above prose.
- [x] 6. Measured on a real engine: `strata` brief 1 844 709 → 81 145 bytes, 424 → 8 sections, with the arch docs included.
- [x] 7. README + `agent-wiki/2026-10-25-params-review-budget.md` describe the selection; name #597 / the PR.
- [x] 8. `make test-unit` green and `make openspec-validate NAME=params-review-budget` exits 0.
