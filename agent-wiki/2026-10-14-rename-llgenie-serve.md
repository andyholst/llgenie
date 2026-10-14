# 2026-10-14 — the CLI is named after the project: llama_serve.py -> llgenie_serve.py (#251)

## Why

`scripts/llama_serve.py` is the llgenie CLI: card detection, model + engine pick from a registry
of **24** engines, download, serve, and dispatch to a per-engine start script. It builds a
llama.cpp argv on one path only. #82 renamed the brand and deliberately left this file
(`llama-served-unchanged: "…the internal launcher module stays at scripts/llama_serve.py"`), so
the binary became `llgenie` while the module still said llama — the confusion #251 describes.

## What changed

- **`git mv`** to `scripts/llgenie_serve.py`, and `tests/test_llama_ai.py` ->
  `tests/test_llgenie_serve.py` with its `llama_ai` alias renamed (291 references tree-wide);
  29 live files updated in total.
- **A compatibility shim** at the old path: `import scripts.llama_serve` returns the real module
  (`sys.modules` alias — object identity holds, verified by a test), and running it runs the CLI
  (verified by executing `--help`). Removed in a follow-up.
- **The seams split**: `scripts/env_seam.py` gives llgenie's own knobs llgenie's name
  (`LLGENIE_BACKEND`, `LLGENIE_RAM_BYTES`, `LLGENIE_MODELS_ROOT`, `LLGENIE_SPEC_DRAFT_P_MIN`,
  `LLGENIE_HEADROOM_BYTES`) with the `LLAMA_*` spellings still honoured, new name winning; an
  empty new value means "unset" so the alias still applies. `detect_server --backend/--ram-gb`
  now exports the new spellings for child processes.
- **Untouched on purpose**: `llama-server`, its `~/bin` shim, `scripts/build_llama_server.sh`,
  the `llama.cpp*` params/Dockerfiles, and `LLAMA_SERVER`/`LLAMA_SERVER_TREE`/`LLAMA_CUBLAS`/
  `LLAMA_HOST` — those name llama.cpp, not llgenie. Dated `agent-wiki/` notes and merged
  `openspec/changes/` are history and stay as written.
- **A guard** (`tests/test_rename_llgenie_serve.py`): no live file may name the old module
  again, the upstream names must still be present, the shim must be the same object, and every
  recorded seam pair must be read by real code (no aspirational aliases).

## Verification

- `make openspec-validate NAME=rename-llgenie-serve` valid; `make lint` OK;
  `make check-wiring` OK (92 documents, 54 tests, 38 scripts — the new script and test are
  wired, no dead definitions).
- **281 passed**: the guard/seam file, the renamed CLI suite, and `test_detect_server` — the
  last of these still uses the `LLAMA_*` spellings throughout, so it doubles as the alias
  regression.
- **Host A/B, behaviour-neutral**: `--dry` captured with the pre-rename launcher and with a
  launcher built from this branch (installed into a scratch `BIN`, so the host's own `~/bin`
  was not repointed) is **byte-identical** for `--engine llama.cpp` *and* `--engine strata` —
  a llama.cpp engine and one that is not.
- `tests/test_install.py` needs a real `make install` (it fails 6/7 on clean `main` inside the
  container too — host-only, unchanged by this work).

## Boundary

The rename is naming only: no serving logic, no registry data, no images. The shim's removal is
a follow-up, and `~/.hermes/profiles/llama-ai/` (a Hermes profile name, not a file in this repo)
is a separate decision.
