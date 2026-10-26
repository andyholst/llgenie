# check-wiring-json — proposal

Issue: [#395](https://github.com/asimov-agent/llgenie/issues/395)

## Why

`python3 scripts/check_wiring.py json` — the machine-readable form of the wiring graph — never
worked. It read `g["named_by_target"]`, a key `graph()` computes but does not return, so it died with
`KeyError: 'named_by_target'`; with that fixed it died again with
`TypeError: Object of type set is not JSON serializable` on `workflow_targets`. A consumer that wants
the wiring graph in code has no working entry point, and the failure looks like "the tool is broken"
rather than a wiring finding.

## What Changes

- `scripts/check_wiring.py` — `graph()` returns `named_by_target` (one source of truth, instead of a
  finding-free local), and the `json` branch serialises `workflow_targets` as sorted lists.
- `tests/test_wiring.py` — a case that runs `json` on the real tree, parses the output, asserts the
  three documented keys, and asserts no value is a set. Verified RED on the pre-change tree.

## Benefit

The wiring graph is consumable: an agent or a script can ask "which target names this document, and
which workflow calls it" without re-implementing the parser, and the subcommand cannot silently rot
because the test reads its output the way a consumer does.
