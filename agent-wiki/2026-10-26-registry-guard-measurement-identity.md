# 2026-10-26 — the additive-only gate compares identity, so the weekly sync can land

Issue: [#668](https://github.com/asimov-agent/llgenie/issues/668) (unfreezes [#534](https://github.com/asimov-agent/llgenie/issues/534))
PR: [#671](https://github.com/asimov-agent/llgenie/pull/671)
OpenSpec: `openspec/changes/registry-guard-measurement-identity`

## What was wrong

`make check-registry-keys` (`scripts/registry_keys.py`) compared each measurement by its exact
`(engine, hardware)` pair and failed on a lowered t/s or engagement counter. Measured today against
upstream `master` (`4eb28c1`, store `2026-10-26T11:56:20Z`) it reported **47 losses** and the weekly
`registry-sync` had not opened a PR since 2026-10-13 — llgenie vendored 23 models / 24 engines against
upstream's 106 / 40.

Almost none of the 47 was a loss:

- 18 of the 24 "measurement … is gone" findings named a `source_post` still in the store; upstream had
  only refined the hardware label (`DFlash2 on RTX 6000` → `RTX 6000 24GB`). The other 6 posts were in
  the store too, re-attributed to a split model row or demoted to `engagement.seen_posts`.
- 10 "counter lowered" were live X re-scrapes — `DFlash2 on RTX 4090 24GB likes 21 → 4` while comments
  (3 → 8), reshares (5 → 72) and views (5451 → 12267) rose on the same post.
- 10 "key 'engagement.seen_posts.*' is gone" came from one model whose derived placeholder upstream
  rebuilt to `[]`; the union of an empty list is an empty set.

#534 read the freeze as an upstream data loss. It is the guard over-firing.

## What changed

- **Identity is the post.** `post_key()` takes the `/status/<id>` of a `source_post`; `post_stats()`
  indexes every tracked post ACROSS THE STORE (`engines[]` + `engagement.seen_posts`), so a relabel, a
  re-attribution to a split model row and a row moving between ranked and seen-only are the same
  measurement. A profile link carries no `/status/<id>` and is not an identity.
- **The engine is the unit that can thin the list** (`rank_engines` groups by it): an engine that had a
  measurement on a model and has none now is a finding.
- **`drift()`** returns a surviving post's lowered t/s, a decreased counter and a shrunken placeholder;
  the CLI prints them as `NOTE:` with both numbers and exits 0. A lowered stated footprint
  (`weight_gb` / `context_tokens` / `system_ram_min`, model or measurement) stays fatal — it is static
  data about a run, not a re-read.
- **`DERIVED_LISTS = ("seen_posts",)`** — its element keys carry no stored data.
- Tests updated in place (`tests/test_registry_keys.py`): every real loss still fails; each
  false-positive class passes; the CLI exits 0 on a drifted sync; the vendored store is additive against
  itself.

## Verified

- **Against the real store**: `python3 scripts/registry_keys.py --cur <upstream>/data/models.json` exits
  **0** with `OK: additive only — nothing lost … (106 models, 81 note(s))`. The pre-change code exits
  **1** with `FAILED: 47 loss(es)` on the same pair — that is the freeze, reproduced and removed.
- `tests/test_registry_keys.py` + `tests/test_registry_footprint.py`: **23 passed** in `llgenie/test:latest`.
- `make test-unit`: **5201 passed, 6 deselected in 1595.65s**. `make lint` (LINT OK), `make
  check-registry-keys` (OK, 23 models, 0 notes), `make check-docs` (200 targets), `make check-wiring`
  (202 documents, 220 make targets), `make check-pr-hygiene`, and `make openspec-validate
  NAME=registry-guard-measurement-identity` (valid) all exit 0.
- The first `make test-unit` run reddened one existing case —
  `tests/test_registry_footprint.py::test_a_measurement_footprint_that_disappears_is_a_loss` — because
  that measurement has no status post, so the store-wide post index cannot see it. `_unposted_footprint_losses()`
  keeps the `(engine, hardware)` footprint comparison for exactly those rows (a profile link or an
  absent `source_post`), which restores the guarantee without re-introducing the relabel defect.

## What this exposes next

The real weekly sequence was run in a throwaway worktree at `369ccda` against the live upstream store:

```
make sync-registry            # exit 0: 23 models -> 106 models (2026-10-26T11:56:20Z)
make check-registry-keys      # exit 0: OK — additive only (106 models, 81 notes)
make render-trend-list-matrix # exit 0: rewrote the 81-case fixture from the new store
make check-engine-skill-gap   # exit 1: 16 registry engines have no skill and no dated decision
```

So the guard is no longer what holds the sync shut; the next gate is `check-engine-skill-gap` on 16 new
upstream engines (`Janas`, `Kapitsa`, `LM Studio`, `MTPLX`, `OpenJet`, `OpenVINO`, `SonicBoom`,
`TandemLLM`, `TokenSpeed`, `Magnitude`, `LemonSeed Engine`, `turbo-fieldfare`, `strixite`, and three
`llama.cpp` forks). Filed as [#673](https://github.com/asimov-agent/llgenie/issues/673) — a decision per
engine (skill or a dated `data/unsupported-engines.json` entry), not part of this change.

## Not in this change

The pick semantics that read this data — `fits()` gating on `vram_tier` (a label) instead of
`vram_min`, the global rather than tier-local list order, and the unvendored `data/MODEL_CONTRACT.md` /
`data/model_contract.json` — are filed as [#669](https://github.com/asimov-agent/llgenie/issues/669).
The matrix grid (no 12/32 GB case) is #228, the view filter #227. The 106-model sync itself is the
weekly `registry-sync` job's action now that this gate passes.
