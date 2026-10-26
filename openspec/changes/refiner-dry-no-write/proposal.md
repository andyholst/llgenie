# refiner-dry-no-write — proposal

Issue: [#352](https://github.com/asimov-agent/llgenie/issues/352)

## Why

`make issue-refiner-pick DRY=1` prints `refine-in.md written` and mutates the checkout it is
previewing: `--dry` skips the claim comment, but the file write sits outside the `if not dry:` block
(`scripts/issue_refiner.py`), so a preview leaves an untracked, gitignored file — and the rename guard
(#350) reads gitignored files, so the preview can also redden an unrelated test.

## What Changes

- `scripts/issue_refiner.py::pick()` — in DRY mode it prints the pick and the destination it *would*
  write, returns `{"dry": True}`, and writes nothing.
- `tests/test_issue_refiner.py` — a case that asserts the file does not exist after a dry pick and
  does after a real one; RED on the pre-change tree.

## Benefit

`DRY=1` is a preview again: no file, no dirty tree, no second-order effects on other gates.
