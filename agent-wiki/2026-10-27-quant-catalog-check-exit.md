# 2026-10-27 — a check whose exit code is discarded is not a gate

Implements issue #701 (OpenSpec change `quant-catalog-check-exit`).

## What was wrong (measured)

`make check-quant-catalog` reported success on a stale table. The generator's `main()` returns 1 when the
committed table differs from what it produces; its `__main__` threw that away:

```python
if __name__ == "__main__":
    main()
```

On `main` @ `3e63bb3`:

```
$ make check-quant-catalog ; echo "exit=$?"
FAIL: data/trending-quant-catalog.json is stale (run make sync-quant-catalog)
--- committed
+++ generated
@@ -1570,127 +1570 @@
-  { "repo": "ddalcu/Qwen3.8-Flash-Next-MLX-Serve-mixed-4-8bit", ... }
exit=0
```

Both consumers believed it: `make ci-unit` (every PR) and the `registry-sync` job's step 9, which runs
`check-quant-catalog` before `test-unit`. The HF class table `llgenie --pick` reads had drifted from the
live Hub behind a green check.

## What was decided

- `raise SystemExit(main())` — the status reaches `make`, therefore CI.
- Regenerate the table the broken check was hiding, with the committed generator (`make sync-quant-catalog`);
  the dropped entries are repos that no longer resolve upstream.
- A guard for the whole class: `tests/test_script_exit_codes.py` parses every `scripts/*.py` and fails when a
  `__main__` calls `main()` bare while `main()` returns a value. `scripts/llgenie_serve.py` calls `main()`
  bare and stays green because its `main()` returns nothing — the guard encodes that distinction instead of
  a list of exceptions.

## Verified

- The guard fails on the pre-fix tree, naming `scripts/gen_trending_quant_catalog.py:273`; passes after the
  one-word change, plus two cases proving it catches a synthetic copy of the shape and ignores a `main()`
  that returns nothing.
- `make check-quant-catalog` on the stale table: exit **2** after the fix (was 0). On the regenerated table:
  exit 0.
- `make test-unit`, `make check-docs`, `make lint`, `make check-wiring` and
  `make openspec-validate NAME=quant-catalog-check-exit` recorded in `tasks.md`.

## Status

Implementation complete on `fix/check-quant-catalog-exit`. Not in this change: why upstream stopped serving
that repo (the sync's business, #677/#687) and the registry sync landing (#669/#677).
