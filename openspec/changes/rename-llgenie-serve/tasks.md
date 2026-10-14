# Tasks

- [x] 1. Write the proposal + spec for the rename (issue #251).
- [x] 2. `git mv scripts/llama_serve.py scripts/llgenie_serve.py` and `tests/test_llama_ai.py`
      -> `tests/test_llgenie_serve.py` (history preserved).
- [x] 3. Add the compatibility shim at the old path (`sys.modules` alias, `__main__` ->
      the CLI), documented as removed in a follow-up.
- [x] 4. Tree-wide rename of the module name and the test alias across live files (29 files),
      leaving `llama-server`, `build_llama_server.sh`, `LLAMA_SERVER*`/`LLAMA_CUBLAS`/`LLAMA_HOST`
      and the history untouched.
- [x] 5. Add `scripts/env_seam.py` and route llgenie's own knobs through it
      (`LLGENIE_MODELS_ROOT`, `LLGENIE_SPEC_DRAFT_P_MIN`, `LLGENIE_HEADROOM_BYTES`) plus
      `detect_server`'s `LLGENIE_BACKEND`/`LLGENIE_RAM_BYTES`, each accepting the legacy
      `LLAMA_*` spelling; `detect_server --backend/--ram-gb` now exports the new spellings.
- [x] 6. Add the guard + seam tests (`tests/test_rename_llgenie_serve.py`) and wire them into
      the test recipes.
- [x] 7. Verify: `make lint`, `make check-wiring`, `make openspec-validate`, the affected
      suites (281 passed for the CLI, guard and detect_server), and a host `make install`
      followed by `--dry` for a llama.cpp engine and for strata (plans unchanged).
- [x] 8. Update the README/AGENTS references, add the agent-wiki note, commit as one atomic
      change, push, and open the PR against `asimov-agent/llgenie` linking #251 (never merge).
