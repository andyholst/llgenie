# 2026-11-07 — engine-build: per-cell disk floor (a flat 30G cannot protect an oversized cell) (issue #1915)

Issue: [#1915](https://github.com/asimov-agent/llgenie/issues/1915)
OpenSpec: `openspec/changes/engine-build-disk-headroom-per-cell`
PR: *(this change — ready-for-review at the fix head)*

## What changed

Main-head engine-build run `42326740375` (`workflow_dispatch`, head `05a4f2fd`) — cell
`engine-build-tensorrt-llm-cuda` — failed `no space left on device` writing
`tensorrt_llm/libs/libth_common.so`, despite passing the #1893 `Disk headroom` gate at **107 GiB free**
(flat 30 GiB floor) on the 145 GiB host. The flat floor is a false-green for an oversized cell: a
single cell's build + export needs the whole host, which a 30 GiB gate cannot express.

The disk policy became **per-cell and committed**:

- `scripts/engine_image.py` adds `OVERSIZED_DISK_GB` (the measured-oversized CUDA cells: tensorrt-llm
  / sglang / strata / tensorfold) and `disk_floor_gb()`; `matrix()` emits `disk_floor_gb` on every
  buildable row (default 30).
- `.github/workflows/engine-build.yml`'s `Disk headroom` step reads
  `LLGENIE_DISK_FLOOR_GB: ${{ matrix.disk_floor_gb }}` instead of a flat `"30"`, so an oversized cell
  that cannot fit the runner fails fast with the readable df verdict instead of a 13-minute ENOSPC.

## Why this shape

The #1893 gate was the right design but flat. An oversized cell's build needs the whole runner; only a
per-cell floor names that honestly and fails the cell in seconds when it cannot fit. No gate was
weakened; the change only makes the disk policy truthful per cell. The rocm cell (`freetoken-rocm`) is
deliberately **out of scope** — it is routed to issue #1696 and is absent from `OVERSIZED_DISK_GB`.

## Measured verification (this lane, at the fix head `09178a61` + diff)

- New test `test_the_disk_floor_is_per_cell_not_a_flat_constant` — **mutation-proved**: FAILS when the
  workflow is reverted to a flat `"30"` and when `tensorrt-llm/cuda` is dropped from `OVERSIZED_DISK_GB`;
  PASSES clean.
- Container suite `test_engine_build_workflow.py` + `test_engine_image_matrix.py` +
  `test_engine_build_timeouts.py` + `test_engine_force_rebuild.py` = **67 passed**.
- YAML parses in the container (`LLGENIE_DISK_FLOOR_GB: ${{ matrix.disk_floor_gb }}`).

## Real per-cell result on the run that filed #1915 (run 138 = `42326740375`)

23 / 27 cells passed; the **4 failures**: `freetoken-rocm` (ENOSPC — rocm cell, #1696),
`tensorrt-llm-cuda` (ENOSPC despite 107 GiB free — this PR's per-cell floor now fails it fast or
names the host it needs), `mlx-cpu` (host-verify NO ANSWER) and `tensorfold-cuda` (flag probe — passes
alone in run 139, so the parallel-sweep resource class) — the latter two are a separate topic under
#1915's umbrella measurement, not this disk change.

## Left open for the dispatcher

A green re-run of `engine-build` at the merged head (the workflow reads its file from `main`) is owned
by the dispatcher lane post-merge; the per-cell floor is verified by the mutation + suite above, and
the real matrix can only be re-quoted from a main-head dispatch.
