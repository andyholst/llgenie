# A live-Hub case asserts the invariant, not an upstream name

Issue: #575. PR: (opened with this change).

Every open PR was red on both OSes for two cases that read live upstream data:

- `tests/test_trend_pick.py` pinned the exact Hub filename `gemma-4-E2B-it.litertlm`; the repo now serves
  `gemma-4-E2B-it_NPU_Uncompiled.litertlm` (2026-10-24), so the `endswith` failed. It now pins the format
  suffix — which build upstream publishes is not ours to assert.
- `tests/test_registry_sync_trend.py` required that the highest-raw-t/s engine for qwen3.8-27b is an engine
  with no skill; the live registry no longer lists one there, so that half had no witness. It now asserts
  what still holds: the raw maximum is not the shown t/s and its engine is not the recommendation. The
  unskilled-engine rule remains the `not ranked_names & no_image` assertion.

Verified locally against the live Hub and registry: the six cases pass (`pytest
tests/test_registry_sync_trend.py::test_live_sync_adopts… tests/test_trend_pick.py::test_plan_download_per_format_live_hub`).
