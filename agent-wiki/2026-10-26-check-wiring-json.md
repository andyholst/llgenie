# 2026-10-26 — the wiring graph's JSON form works

Issue: [#395](https://github.com/asimov-agent/llgenie/issues/395)
OpenSpec: `openspec/changes/check-wiring-json`

## What was wrong

Two defects in one subcommand:

```
$ python3 scripts/check_wiring.py json
KeyError: 'named_by_target'          # graph() computed it but never returned it
$ … after that was patched
TypeError: Object of type set is not JSON serializable
when serializing dict item 'workflow_targets'
```

## What changed

- `graph()` now returns `named_by_target` (the `check` path and the `json` path share one computation).
- The `json` branch serialises `workflow_targets` as sorted lists.
- `tests/test_wiring.py` runs the subcommand on the real tree, parses its output, asserts exactly the
  three keys and that every value is a list.

## Verified

- RED on the pre-change tree: `1 failed`; after the fix: `11 passed`.
- `python3 scripts/check_wiring.py json > /tmp/wiring.json` → rc 0, keys
  `['named_by_target', 'reachable', 'workflow_targets']`, 219 targets, 19 workflows.
