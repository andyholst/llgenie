# A live-Hub case asserts the invariant, not a filename upstream renames

## Why

Two cases in the hermetic unit gate read live upstream data and pinned it too tightly, so an upstream
change reddened every open PR on both OSes while the tree was fine (issue #575):

```
FAILED tests/test_registry_sync_trend.py::test_live_sync_adopts_a_higher_skilled_tps_for_models_that_fit_48gb
FAILED tests/test_trend_pick.py::test_plan_download_per_format_live_hub[gemma-4-e2b-litertlm-…]
2 failed, 5075 passed
```

- `tests/test_trend_pick.py` pinned the exact Hub filename `gemma-4-E2B-it.litertlm`; on 2026-10-24
  `litert-community/gemma-4-E2B-it-litert-lm` serves `gemma-4-E2B-it_NPU_Uncompiled.litertlm`, so the
  `endswith` assertion failed. Which build a repo publishes is upstream's business; the invariant is the
  FORMAT (`.litertlm`) and the repo — plus "the generic build, not gpu/web/vendor", which is already
  asserted through `_LITERT_VARIANT`.
- `tests/test_registry_sync_trend.py` asserted that the engine holding the highest raw t/s for
  `qwen3.8-27b` is an engine with **no skill**. The live registry no longer lists one there (every engine
  it lists for that model is installed by a skill), so the assertion had no witness left. The rule it
  meant to prove — an unskilled engine is never the recommendation — is the
  `not ranked_names & no_image` assertion, which still holds; the surviving claim that needs pinning is
  that the raw maximum is not what the list shows.

Both reproduced locally on a branch whose diff touches neither file's subject, and on both open PRs
(#572 run `40070197776`, #574 run `40070180582`).

## What Changes

- **`tests/test_trend_pick.py`** — the litertlm case pins the format suffix, not the file name.
- **`tests/test_registry_sync_trend.py`** — the "raw maximum is not the recommendation" half is asserted
  from the payload (the highest-t/s engine is not the shown one), and the unskilled-engine rule stays as
  the `no_image` check. No skip, no loosened pass.
- **README** — the live-read tests document that their expectations follow the payload.

## Impact

- An upstream rename or a new measurement no longer reddens the unit gate on every PR; a genuine
  regression in picking still fails these cases.
