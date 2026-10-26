# 2026-10-26 — a dry refiner pick writes nothing

Issue: [#352](https://github.com/asimov-agent/llgenie/issues/352)
OpenSpec: `openspec/changes/refiner-dry-no-write`

## What was wrong

`--dry` skipped the claim comment but the `out_path.write_text(render(...))` sat outside the
`if not dry:` block, so `make issue-refiner-pick DRY=1` wrote `refine-in.md` into the checkout it was
previewing (and the rename guard, which walks the tree, then saw a file it should not).

## What changed

`pick()` in DRY mode prints the issue and the destination it would write, returns `{"dry": True}`, and
writes nothing. `tests/test_issue_refiner.py` asserts both halves: no file after a dry pick, the file
after a real one.

## Verified

- RED on the pre-change tree: `1 failed, 21 passed`; after the fix `22 passed`.
