# rebase-bot decision

## ADDED Requirements

### Requirement: one PR's merge state resolves to exactly one of four outcomes

`rebase_bot_sweep.outcome(state, crashed=False)` MUST return `REBASE` for `BEHIND`/`DIRTY`, `NONE` for a
computed state that needs no rebase, `DEFER` for `UNKNOWN`, and `ERROR` when the read itself crashed —
including when the state it managed to read looks rebasable.

#### Scenario: an uncomputed state is deferred, never treated as nothing to do

- **Given** a PR whose `mergeStateStatus` is `UNKNOWN`
- **When** the sweep classifies it
- **Then** the outcome is `DEFER` and the PR is named as deferred to the next run

#### Scenario: a crashed read is an error, not a rebase and not nothing

- **Given** a read that raised while the sweep was classifying a `DIRTY` PR
- **When** the sweep classifies it
- **Then** the outcome is `ERROR`, the run exits non-zero, and the PR is named in the failure
