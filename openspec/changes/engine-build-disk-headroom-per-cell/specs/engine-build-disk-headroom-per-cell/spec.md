# engine-build-disk-headroom-per-cell

## ADDED Requirements

### Requirement: every buildable cell names its own disk floor

The flat `LLGENIE_DISK_FLOOR_GB` floor is a false-green for an oversized cell — a 30 GiB floor passed
a cell at 107 GiB free that then ENOSPC'd 17 minutes later on a 145 GiB host (issue #1915, run
`42326740375`). The engine-build matrix MUST carry a per-cell `disk_floor_gb` (committed in
`engine_image.py`'s `OVERSIZED_DISK_GB`, default 30), and the `Disk headroom` step MUST read it, so an
oversized cell that cannot fit the runner fails fast with the df verdict instead of after the build
exhausts the disk.

WHEN the engine-build `matrix` job produces its rows
THEN every buildable row carries a `disk_floor_gb` (the committed `OVERSIZED_DISK_GB` policy for the
cells whose build + export genuinely exceed a stock runner; the default 30 for ordinary cells).

AND WHEN the `Disk headroom` step sets its floor env
THEN it MUST be `LLGENIE_DISK_FLOOR_GB: ${{ matrix.disk_floor_gb }}` (per-cell), not a flat constant.

#### Scenario: an oversized cell that cannot fit the runner fails fast

- **Given** the `Disk headroom` step with the per-cell floor from the matrix
- **When** a cell whose `disk_floor_gb` exceeds the runner's free disk begins
- **Then** the step exits non-zero with the `df -h /` line and a `::error::` annotation naming the
  cell and its per-cell floor — the cell reds immediately, not 17 minutes later with ENOSPC
- **Test:** `test_the_disk_floor_is_per_cell_not_a_flat_constant` asserts the workflow reads
  `${{ matrix.disk_floor_gb }}`, every buildable row carries it, and the measured-oversized
  `tensorrt-llm/cuda` row carries a floor `>= 120` (its 107-GiB pass on the flat 30 was insufficient);
  the default-30 ordinary cell (ollama/cpu) is unchanged so no ordinary cell is newly reddened
