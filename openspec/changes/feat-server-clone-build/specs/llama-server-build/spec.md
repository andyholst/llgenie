# feat-server-clone-build — spec of record

## ADDED Requirements

### Requirement: card RAM selects the llama.cpp tree
The build system MUST select the llama.cpp fork from **card RAM only**, never by
inspecting the downloaded model's quant/filename. "Card RAM" means the NVIDIA
GPU's VRAM when an NVIDIA card is present (`nvidia-smi --query-gpu=memory.total`),
otherwise the system RAM.

#### Scenario: 24 GB inclusive boundary picks Prism
- **Given** a card with exactly 24 GB of RAM (16 GB NVIDIA VRAM is also <= 24 GB)
- **When** the tree is selected from card RAM
- **Then** the tree is `prism` (inclusive lower bound)

#### Scenario: above 24 GB picks upstream
- **Given** a card with 25 GB (or 48 GB / 64 GB) of RAM
- **When** the tree is selected from card RAM
- **Then** the tree is `upstream`

#### Scenario: low-end cards pick Prism
- **Given** an 8 GB or 12 GB or 16 GB card
- **When** the tree is selected from card RAM
- **Then** the tree is `prism`

#### Scenario: GPU VRAM, not system RAM, is the card RAM on an NVIDIA card
- **Given** a machine with a 16 GB NVIDIA GPU and 64 GB of system RAM
- **When** card RAM is read
- **Then** the value is the GPU's VRAM (16 GB), yielding `prism`, not the 64 GB
  system RAM value (which would yield `upstream`)

### Requirement: hardware selects the backend
The build system MUST select the backend from the hardware using the real tools:
- **metal**: macOS + Apple Silicon (`sysctl hw.machinetype` / `uname -m`)
- **cuda**: `nvidia-smi -L` lists a GPU **and** `nvcc` (the compiler) is installed
- **cpu**: fallback (no usable GPU path)

#### Scenario: cuda requires both a GPU and nvcc
- **Given** an NVIDIA GPU is listed by `nvidia-smi` but `nvcc` is NOT installed
- **When** the backend is detected
- **Then** the backend is `cpu`, not `cuda`

#### Scenario: cuda when both are present
- **Given** `nvidia-smi -L` lists a GPU and `nvcc` is on PATH (or in
  `/opt/cuda/bin` / `/usr/local/cuda/bin`)
- **When** the backend is detected
- **Then** the backend is `cuda`

#### Scenario: metal on Apple Silicon
- **Given** macOS with Apple Silicon (`sysctl hw.machinetype = arm64`)
- **When** the backend is detected
- **Then** the backend is `metal`

#### Scenario: CPU fallback
- **Given** a machine with no NVIDIA GPU and no Metal path
- **When** the backend is detected
- **Then** the backend is `cpu`

### Requirement: env seams for detection
The detection MUST expose three env-var seams (mock the hardware without
touching it), used by tests and the parallel CI variant jobs:
- `LLAMA_BACKEND` = metal | cuda | cpu
- `LLAMA_RAM_BYTES` = card RAM in bytes
- `LLAMA_SERVER_TREE` = prism | upstream (forces the tree, independent of RAM)

#### Scenario: backend override
- **Given** `LLAMA_BACKEND=cuda` is set
- **When** the backend is detected
- **Then** the backend is `cuda` regardless of the real hardware

#### Scenario: tree override forces a tree independent of RAM
- **Given** an 8 GB card (which would normally pick `prism`) with
  `LLAMA_SERVER_TREE=upstream`
- **When** the tree is selected
- **Then** the tree is `upstream`
#### Scenario: unknown override falls back to RAM
- **Given** `LLAMA_SERVER_TREE=not-a-tree` on an 8 GB card
- **When** the tree is selected
- **Then** the RAM-based decision stands (`prism` for 8 GB)

### Requirement: clone-or-pull to the latest commit
The build MUST clone the selected tree if absent, or fetch and reset to the
branch tip if present. It MUST never build a stale prebuilt tree.

#### Scenario: fresh clone
- **Given** the selected tree directory does not exist
- **When** the build runs
- **Then** the tree is cloned at the latest commit of its branch

#### Scenario: existing tree is pulled
- **Given** the selected tree directory already exists
- **When** the build runs
- **Then** the tree is fetched and reset to the branch tip before building

### Requirement: per-backend build dirs (parallel-safe)
Each backend build MUST write into its own per-backend dir (`build-cpu`,
`build-cuda`, `build-metal`) so parallel variants never collide.

#### Scenario: distinct build dirs
- **Given** the same card built for cpu, cuda, and metal
- **When** `detect_all` is run for each backend
- **Then** the build dirs are `build-cpu`, `build-cuda`, `build-metal`
  respectively, each with the matching CMake flags

### Requirement: build verifies the binary
The build MUST verify the resulting `llama-server` binary exists, responds to
`--help` (exit 0), and — for the cuda variant — links against CUDA runtime
libraries (`libcuda.so.1`, `libcudart`, `libcublas`).

#### Scenario: binary exists and --help works
- **Given** a successful build
- **When** the binary is checked
- **Then** the binary exists and `--help` exits 0

#### Scenario: cuda binary links cuda libs
- **Given** a cuda variant build
- **When** the binary is checked for CUDA linkage
- **Then** it links against at least one CUDA runtime library

### Requirement: CI builds every tree x backend variant the runner supports, in parallel
The CI pipeline MUST build and verify each supported tree x backend combination
on the appropriate runner, each variant self-contained (own tree dir + build dir),
in parallel GitHub jobs:
- `ubuntu-latest` (Linux, CUDA toolkit installed first):
  `upstream+cpu`, `upstream+cuda`, `prism+cpu`, `prism+cuda`
- `macos-14` (Metal-capable):
  `upstream+metal`, `upstream+cpu`, `prism+metal`, `prism+cpu`

#### Scenario: ubuntu runner builds cuda only after installing the CUDA toolkit
- **Given** the `ubuntu-latest` runner for the cuda variants
- **When** the build job runs
- **Then** the CUDA toolkit (nvcc) is installed BEFORE the CUDA llama.cpp build
  is configured/compiled

#### Scenario: each variant's binary is verified
- **Given** a variant build (tree + backend)
- **When** the build completes
- **Then** the binary exists, `--help` exits 0, and (for cuda) cuda libs are linked

#### Scenario: metal builds only on macOS
- **Given** a metal variant build on a non-macOS runner
- **When** the build attempts the metal backend
- **Then** it fails loudly with a clear "Metal requires macOS" error (no fake pass)

### Requirement: host `make install` builds only the right variant
The host `make install` MUST use the **auto-detected** tree + backend for the
real card (clone-or-pull + build + symlink), not a prebuilt. A host with a
16 GB NVIDIA card builds `prism + cuda` exactly once.

#### Scenario: host auto-detects and builds the right variant
- **Given** a host with a 16 GB NVIDIA GPU + nvcc
- **When** `make install` runs
- **Then** it detects `prism + cuda` and builds exactly that variant, symlinking
  `~/bin/llama-server` to the freshly-built binary

### Requirement: `make install` is locally testable
`make install` MUST be tested on the actual host as an acceptance criterion, and
`make uninstall` must remove exactly what `make install` created (launcher,
symlinks) without deleting repo source.

#### Scenario: uninstall removes only what install created
- **Given** a completed `make install`
- **When** `make uninstall` runs
- **Then** `~/bin/llgenie`, `~/bin/llgenie.py`, and `~/bin/llama-server` are
  removed, the venv and repo source files are untouched, and a fresh
  `make install` works

### Requirement: the selected model's trained context is the server window
When `llgenie` starts `llama-server` for the model the user selected, `-c`
MUST be that model's maximum context, reduced only when the card cannot hold
the KV cache for it.

The ceiling is the selected GGUF's `<arch>.context_length`. Ternary Bonsai 2
(`sudoingx/Ternary-Bonsai-2-27B-PTQ1_0-MTP-GGUF`, architecture `qwen35`)
publishes `context_length` **262144**. On a 16 GB card the KV cache for that
window fits, so `-c` is **262144**. On an 8 GB card the same file does not
fit at 262144, so `-c` is **30720**.

The budget is card RAM from `detect_server.detect_card_ram_bytes()` (NVIDIA
VRAM when a GPU is present, otherwise system RAM; `LLAMA_RAM_BYTES`
overrides), minus the weight file and a 3 GB reserve. It is not the hardcoded
48 GB `TOTAL_RAM_BYTES` constant. Hybrid models that publish
`<arch>.full_attention_interval` charge KV only for the full-attention layers
(language blocks divided by the interval, plus `<arch>.nextn_predict_layers`
when the file has an MTP block) and use `<arch>.attention.key_length` /
`value_length` as the head dimension. A dense model with no interval counts
every block, with head dim `n_embd // n_head`. The result is rounded down to
a multiple of 1024 and is never below 2048. A missing `context_length` caps
the window at 32768.

`main` and `_serve_chosen` both call `serve_context` and pass the result to
`llama-server` as `-c`. That `-c` is the runtime window (`n_ctx` on
`/props`). A client of this server, including the Hermes `local-llm` profile,
compacts against that runtime window: the profile's Jev engine threshold is
0.60 of the probed `n_ctx`, so compression runs before the prompt fills the
window `llgenie` allocated.

#### Scenario: Bonsai on a 16 GB card gets its trained 262144 window
- **Given** a GGUF shaped like Ternary-Bonsai-2-27B-PTQ1_0-mtp
  (`context_length` 262144, 65 blocks, `full_attention_interval` 4,
  `nextn_predict_layers` 1, key and value length 256, 4 KV heads, about 6.5 GB)
- **When** it is served on a 16 GB card
- **Then** `-c` is 262144

#### Scenario: a card that cannot hold the trained window gets a smaller context
- **Given** the same Bonsai-shaped model
- **When** it is served on an 8 GB card
- **Then** `-c` is 30720, which is below 262144, a multiple of 1024, and at least 2048

#### Scenario: a missing context_length caps at 32768
- **Given** a dense model whose header has no `context_length`
- **When** it is served on a 48 GB card
- **Then** `-c` is 32768

#### Scenario: the header reader keeps the hybrid fields
- **Given** a qwen35 GGUF header with `context_length` 262144, `key_length` 256,
  `value_length` 256, `full_attention_interval` 4, and `nextn_predict_layers` 1
- **When** `read_model_meta_fast` parses it
- **Then** those fields are on the meta dict and `serve_context` on a 16 GB card
  returns 262144

### Requirement: MTP (spec-decode) knobs are card-driven
When a model carries an MTP (multi-token-prediction) draft head — detected as
`meta["nextn_layers"] > 0` in the GGUF (`nextn_predict_layers`), e.g.
Ternary-Bonsai-2 MTP / Qwen3.8-27B MTP — the launcher MUST engage `llama-server`'s
`--spec-type draft-mtp` path and set the community-mapped speed knobs from the
**card's RAM** (the same `detect_card_ram_bytes()` value that picks the tree),
never from hard-coded constants. Grounded in the qwen38-mtp community rules:

- **Depth (`--spec-draft-n-max`) is card-class driven.** `mtp_depth_for_card`
  returns `1` when card RAM `<= 16 GB` (8/12/16 GB — shallow: pays everywhere,
  no starved depth-2 risk), `2` when `16 GB < card RAM <= 24 GB` (24 GB
  inclusive), and `3` when card RAM `> 24 GB` (32/48/64/128/… GB). A hermetic
  unit test asserts each bin boundary against a mocked card-RAM seam (no real
  GPU required).
- **`--spec-draft-p-min` is never a default.** Emitted **only** when the seam
  `LLAMA_SPEC_DRAFT_P_MIN` env is set (community rule 2: it helps starved cards
  and hurts fast ones — a knob, never a constant). Unset => flag absent.
- **MTP pins `--parallel` to 1 regardless of model size.** When the MTP head is
  engaged, `-np 1` even for a small model (the size-based `-np 2` for models
  `< 10 GB` must NOT apply). When MTP is absent, the size-based rule stands:
  2 slots for models `< 10 GB`, 1 slot for `>= 10 GB`. (Community rule 5:
  speculative decode is a single-stream optimisation; `--parallel > 1` kills the
  gain and inflates the baseline.)

#### Scenario: a 24 GB card with an MTP model gets n-max 2
- **Given** a model with `nextn_layers > 0` served on a 24 GB card
- **When** `build_command` runs with `card_bytes = 24 * GiB`
- **Then** the argv contains `--spec-type draft-mtp`,
  `--spec-draft-n-max 2`, and `-np 1`

#### Scenario: a small MTP model still pins -np 1 (rule 5)
- **Given** a model with `nextn_layers > 0` and `size_gb < 10` on a small card
- **When** `build_command` runs
- **Then** `-np 1` is emitted (the size-based `-np 2` for small models is
  suppressed because MTP is a single-stream path)

#### Scenario: p-min is off by default, on only via the seam
- **Given** an MTP model with `LLAMA_SPEC_DRAFT_P_MIN` unset
- **When** `mtp_spec_flags` runs
- **Then** no `--spec-draft-p-min` flag is present; with the seam set (e.g.
  `0.7`) the flag is emitted with that value

#### Scenario: a model without an MTP head emits no spec flags
- **Given** a model with `nextn_layers == 0`
- **When** `build_command` runs
- **Then** the argv contains no `--spec-type` / `--spec-draft-n-max` /
  `--spec-draft-p-min` flags, and the size-based `-np` rule (2 slots `< 10 GB`)
  applies

#### Scenario: depth follows the same card RAM that picks the tree
- **Given** the same MTP model on an 8 GB card vs a 64 GB card
- **When** `build_command` runs for each card (card_bytes passed or detected via
  `detect_card_ram_bytes`)
- **Then** `--spec-draft-n-max 1` on the small card and `--spec-draft-n-max 3`
  on the large card — the knob is a function of the card, not a constant
