# A changed registry opens ONE issue that states what changed

## Why

The weekly `registry-sync` regenerates the store, the README, the vendored contract and four derived
tables and then stops: whenever a gate is red the PR step is `skipped` (measured: run `40450580364`,
`test-unit` 130 failed / 14707 passed, steps 10 and 11 skipped). Nobody is told what changed — learning
that 89 models and 18 engines appeared means diffing a 20k-line JSON by hand.

That is the input #677/#693 are missing: both say "re-derive against the new store", and neither can start
without the change list.

## What changes

`scripts/registry_change_issue.py`, stdlib only, two commands:

- **`report`** compares `HEAD:data/models.json`, `data/model_contract.json`, `data/trending-README.md`,
  `data/trending-quant-catalog.json`, `tests/fixtures/trend-list-matrix.json` and
  `data/engine-skill-gap.json` with the working tree's, and renders the facts: `generated_utc` old → new,
  model/engine counts, added / removed / renamed model ids (capped at 40, then a pointer at the diff), the
  engines new to the registry, the `formats` vocabulary seen, every contract change (required keys added or
  removed per model row, new `backend` enum values), README rows added/removed, and the derived-table
  counts (quant catalog models + links, matrix cases, unresolved engines).
- **`open`** files ONE issue, `sync: review the <generated_utc> trending registry`, labelled
  `agent:implement`, whose body is the report in this repository's issue shape plus a "what this implies"
  checklist: re-derive the trend/pick goldens (#693/#677), decide each new engine (#673/#686), teach the
  contract reader (#694), check the formats vocabulary (#687/#692), run the job's own gates. A hidden
  `<!-- registry-sync-changes: <utc> -->` marker is the identity: a re-run for the same store EDITS that
  issue rather than filing a second.

The workflow runs it with `if: always() && steps.diff.outputs.changed`, so the issue exists whether the
gates passed or reddened — the analysis is most valuable exactly when the store cannot land.

No model in the path: a summariser over a 20k-line diff cannot be re-run to the same answer. The diff is
the artefact; this is its index, and the judgement stays with the agent that picks the issue up.

## Impact

- `scripts/registry_change_issue.py` (new), `Makefile` (`registry-change-report`, `sync-change-issue`, both
  in `.PHONY`, both in `make help`).
- `.github/workflows/registry-sync.yml` — one new step, `if: always() && steps.diff.outputs.changed`, with
  `GH_TOKEN: secrets.BUMP_TOKEN`.
- `tests/test_registry_change_issue.py` — `compare()`/`render()` over two stores built in a temp dir, and
  `open_issue()` with `gh` replaced by a recorder (the external system): update not duplicate, exactly one
  create, `--dry` mutates nothing.
- `README.md` (registry section), `docs/BOTS.md` (the sync flow), `agent-wiki/`, `CHANGES.md`.

Not in this change: the ranking rule the trend list is built on (#669) — which is why the sync does not
land yet — and archiving each sync as a timestamped snapshot (the comparison is against `HEAD`, which is
the previous store).
