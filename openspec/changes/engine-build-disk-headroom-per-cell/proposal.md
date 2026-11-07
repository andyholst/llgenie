# engine-build-disk-headroom-per-cell — the disk floor names what the cell's build must hold

## Why

The #1893 gate turned the pre-build `Free disk` step into a durable `Disk headroom` step with a flat
`LLGENIE_DISK_FLOOR_GB` = 30 GiB floor, and it was the right shape — but a flat floor is a
**false-green** for an oversized cell. Measured on engine-build run `42326740375` (workflow_dispatch,
head `05a4f2fd`): the `engine-build-tensorrt-llm-cuda` cell passed the gate at **107 GiB free**
(floor 30), then ENOSPC'd 17 minutes later (`no space left on device` writing
`tensorrt_llm/libs/libth_common.so`) on the 145 GiB host. A 30 GiB floor cannot express that a single
cell's build + export needs the whole 145 GiB host; the gate either passes (and the build dies later)
or can only guess a per-cell number. Issue #1915 is the reactor-facing report of exactly that failure.

## What changes

`engine_image.py` carries a committed, per-cell disk policy `OVERSIZED_DISK_GB`
(`matrix()` emits `disk_floor_gb` on every buildable row; default 30; the measured-oversized
CUDA cells name their real requirement). `engine-build.yml`'s `Disk headroom` step reads
`LLGENIE_DISK_FLOOR_GB: ${{ matrix.disk_floor_gb }}` instead of a flat `"30"`, so an oversized cell
that cannot fit the runner reds FAST with the readable df verdict instead of a 13-minute ENOSPC.

- `scripts/engine_image.py`: `OVERSIZED_DISK_GB` (+ `disk_floor_gb()`), `matrix()` emits the field.
- `.github/workflows/engine-build.yml`: `Disk headroom` step uses `${{ matrix.disk_floor_gb }}`.
- `tests/test_engine_build_workflow.py`:
  `test_the_disk_floor_is_per_cell_not_a_flat_constant` — mutation-proved (both below).

## Out of scope

- The rocm cell (`freetoken-rocm`) — routed to issue #1696, deliberately absent from `OVERSIZED_DISK_GB`.
- Any engine pin bump; any gate weakening (this *strengthens* only the honest disk policy).
- The `mlx-cpu`/`tensorfold-cuda` flag/host-verify failures in the same run — a separate
  resource/parallel class, tracked under #1915's umbrella measurement, not this disk change.

## Who

ci-pipelines-maintainer (this lane owns the engine-build workflow's disk/mount policy; #1893/#1895
was the prior instance of this class).

## Measured verification (this lane, at the fix head)

- Mutation 1 (workflow reverted to flat `"30"`): new test FAILS (asserts the per-cell env) — restored.
- Mutation 2 (`tensorrt-llm/cuda` floor dropped out of `OVERSIZED_DISK_GB`): new test FAILS (the
  `>= 120` assertion) — restored.
- Clean: `test_engine_build_workflow.py` + `test_engine_image_matrix.py` + `test_engine_build_timeouts.py`
  + `test_engine_force_rebuild.py` = **67 passed** in the `llgenie/test:latest` container.
- YAML parses in the container (`LLGENIE_DISK_FLOOR_GB: ${{ matrix.disk_floor_gb }}`).
