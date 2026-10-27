# 2026-10-27 — `check-quant-catalog` stops failing on what the live Hub re-reads

Implements #736 in the PR that needs it (#732): `ci-unit` fails before `test-unit` runs when
this gate is red, so the pick-gate change could not go green while it was. The two share one
objective — a gate asserts a RULE over the store, never a snapshot of data upstream owns.

## What was measured

- `make check-quant-catalog` exits **2** on `main` (`288c141`), in the user's checkout and in
  a feature worktree alike, so it is not a branch regression: `linux / unit` of PR #732 (run
  40503843456, job 122188542677) died at `make[1]: *** [Makefile:294: check-quant-catalog] Error 1`
  before pytest started.
- The diff is NOT a lost plan. Comparing the two structures: `qwen3.8-flash-next-125b`/MLX
  regenerates the **same 14 plans** (`set(committed) == set(generated)`) in a different
  sequence — `mlx_repos()`/`tensorfold_repos()` query `/api/models?search=…&sort=downloads`,
  and those counts move by the hour. The same regeneration also now offers conversions
  upstream published after the last sync (`ddalcu/…-Serve-*`, `pipenetwork/…mixed-4_8bit`,
  `Sawfwair/…Mixed-2bit`), which is what `make sync-quant-catalog` records.

## What changed

- `scripts/gen_trending_quant_catalog.py`: `compare(committed, generated) -> (failures,
  notes)` decides, and `--check` uses it instead of a byte comparison.
  - **FAIL** — a row the committed table has and the generator no longer produces: a plan
    gone, a plan whose repo/files/size/link changed, an engine's arch list changed, or a
    table rendered for another registry (`meta.generated_utc`). This is the case the gate
    exists for (a hand-edited or lost plan would ship an unverified download).
  - **NOTE** — the live search re-ordered the same plans, or offers a plan/engine/model the
    committed table does not record yet. Printed as `[quant-catalog] NOTE: …`, exit code 0,
    because recording them is the weekly sync's job. This is the rule `registry_keys` already
    applies to data the store re-reads.
- `tests/test_trending_quant_catalog.py`: six hermetic tests drive `compare()` in both
  directions (clean regeneration, an added plan is a note, a REORDER is a note, a lost plan
  fails, a changed plan fails, a catalog rendered for another registry fails).
- Docs: `README.md` (the `make check-quant-catalog` description) and `docs/ARCHITECTURE.md`
  (what "differs" means, next to issue #701's exit-status paragraph).

## Verified

- `make check-quant-catalog` on the committed table: **exit 0**, one note
  (`qwen3.8-flash-next-125b/MLX: the live search lists the same 14 plan(s) in a different
  order — the next sync records it`).
- `tests/test_trending_quant_catalog.py`: **13 passed**.

## Decisions

- **Report, do not fail.** The gate cannot honestly prove a *newer* table than the repository
  owns; it can prove the repository's table still regenerates. A gate that fails on
  upstream's search ordering reds every PR on the repository, which is how this was found.
- **`data/` is untouched.** The plan set is unchanged, so the fix belongs in the checker, not
  in the table; the weekly `registry-sync` still owns every write.
- **Determinism of the order is a separate decision** (see the issue's `Not covered`): sorting
  `mlx_repos()`'s candidates would change the committed table, which the sync owns.
