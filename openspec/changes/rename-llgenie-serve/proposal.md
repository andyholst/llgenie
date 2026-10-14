# Name the CLI after the project it is

## Why

`scripts/llama_serve.py` is the llgenie CLI: it detects the card, picks a model and an engine
from the registry (**24** engines), downloads, serves, and dispatches to a per-engine start
script. It builds a llama.cpp argv on exactly one of its paths. The name says llama, and that
is the confusion issue #251 describes.

This is the loop #82 left open. That change renamed the brand (`llama-ai` -> `llgenie`) and
deliberately stopped at this file: its proposal lists the capability
`llama-served-unchanged: "the served binary and upstream deps are untouched; the internal
launcher module stays at scripts/llama_serve.py"`. The binary became `llgenie`, the module
stayed `llama_serve`, and `llama-server`/`LLAMA_*` (upstream's own names) sit next to them.

## What Changes

- **The module**: `scripts/llama_serve.py` -> `scripts/llgenie_serve.py` (`git mv`, history
  kept), and the test module `tests/test_llama_ai.py` -> `tests/test_llgenie_serve.py` with its
  alias `llama_ai` -> `llgenie_serve` (242 references in that file alone, 291 tree-wide).
- **A one-release compatibility shim** at the old path: importing `scripts.llama_serve` returns
  the real module (`sys.modules` alias, so object identity holds), and running it runs the CLI.
  Any existing script, cron entry or habitual invocation keeps working.
- **The seams split**: llgenie's own knobs take llgenie's name — `LLGENIE_BACKEND`,
  `LLGENIE_RAM_BYTES`, `LLGENIE_MODELS_ROOT`, `LLGENIE_SPEC_DRAFT_P_MIN`,
  `LLGENIE_HEADROOM_BYTES` — with the `LLAMA_*` spellings still accepted as deprecated aliases
  through `scripts/env_seam.py`. Names that are llama.cpp's own (`LLAMA_SERVER`,
  `LLAMA_SERVER_TREE`, `LLAMA_CUBLAS`, `LLAMA_HOST`, `llama-server`, `build_llama_server.sh`)
  are untouched: they are upstream's.
- **A rename guard** (`tests/test_rename_llgenie_serve.py`): no live file may name the old
  module again, while the upstream names are asserted to still be present. History
  (`agent-wiki/` dated notes and merged `openspec/changes/`) is left alone.
- **The installed artifacts**: the `~/bin/llgenie` wrapper, the `~/bin/llgenie.py` symlink and
  `make uninstall`'s "repo untouched" guard all follow the new path; `make install` regenerates
  them, so a reinstall is part of the migration rather than a manual step.

## Capabilities

- **llgenie-serve-naming**: the CLI module, its tests and every live reference carry the
  project's name, with a deprecated shim keeping the old path usable.
- **llgenie-env-seams**: llgenie's own environment knobs are named after llgenie.
- **llama-served-unchanged** (kept from #82): the served binary, the shim and upstream's names
  are untouched.

## Impact

Behaviour-neutral by construction: no serving logic changes, only names, a shim, an alias layer
and a guard test. The verification is a real host run of `--dry` for a llama.cpp engine *and* a
non-llama.cpp engine (strata), which must print exactly the plans they printed before.
