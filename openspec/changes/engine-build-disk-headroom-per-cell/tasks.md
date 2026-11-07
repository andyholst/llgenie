# engine-build-disk-headroom-per-cell — tasks

- [x] `engine_image.py`: add `OVERSIZED_DISK_GB` per-cell disk policy + `disk_floor_gb()`; `matrix()` emits `disk_floor_gb` on every buildable row (default 30); measured-oversized CUDA cells name their real requirement (tensorrt-llm/cuda, sglang/cuda, strata/cuda, tensorfold/cuda). rocm cell (freetoken-rocm) deliberately absent — #1696.
- [x] `engine-build.yml`: `Disk headroom` step reads `LLGENIE_DISK_FLOOR_GB: ${{ matrix.disk_floor_gb }}` instead of a flat `"30"`, so an oversized cell that cannot fit the runner fails fast with the df verdict instead of a 13-minute ENOSPC.
- [x] `test_the_disk_floor_is_per_cell_not_a_flat_constant` in `tests/test_engine_build_workflow.py`; mutation-proved both ways (flat-30 reds; OVERSIZED drop reds; clean green).
- [x] YAML parses in `llgenie/test:latest`; `test_engine_build_workflow.py` + `test_engine_image_matrix.py` + `test_engine_build_timeouts.py` + `test_engine_force_rebuild.py` = 67 passed.
- [x] Docs trio per #1123: `agent-wiki/` note + `docs/changes.d/` fragment; openspec spec + proposal + tasks.
