# live-hub-test-drift

## ADDED Requirements

### Requirement: A live-Hub case asserts the invariant, never an upstream name

A unit case that reads live upstream data SHALL assert the invariant it exists for — the format, the
repo, the ranking rule, "the raw maximum is not the recommendation" — and SHALL NOT pin a value that
upstream may rename or remeasure, unless that value is the thing under test. A case that can no longer
have a witness SHALL keep the rule that still holds instead of failing or skipping.

WHEN upstream renames a file or publishes a new measurement
THEN the live-Hub unit cases still pass, and a real picking regression still fails them.

#### Scenario: an upstream filename change does not fail the download plan

Given the litertlm registry entry, whose Hub repo now serves a differently named build
When  the plan is computed for a 16 GB CUDA card
Then  it is a `.litertlm` file from that repo, not a gpu/web/vendor variant.

- **Test:** `tests/test_trend_pick.py::test_plan_download_per_format_live_hub[gemma-4-e2b-litertlm-litert-community/gemma-4-E2B-it-litert-lm-.litertlm]`

#### Scenario: the raw maximum is not the recommendation

Given the live registry
When  qwen3.8-27b is ranked for a 48 GB CUDA card
Then  the shown t/s is below the raw maximum and the engine owning that maximum is not the
recommendation.

- **Test:** `tests/test_registry_sync_trend.py::test_live_sync_adopts_a_higher_skilled_tps_for_models_that_fit_48gb`
