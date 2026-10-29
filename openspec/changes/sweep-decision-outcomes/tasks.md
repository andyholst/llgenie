# Tasks

- [x] `outcome()` with four outcomes, `crashed` as an argument rather than a separate path.
- [x] The sweep classifies through it (`outcome(state) is not REBASE`), so the rule has one home.
- [x] Tests: `DIRTY`/`BEHIND` → `REBASE`; `MERGEABLE`/`BLOCKED`/`CLEAN` → `NONE`; `UNKNOWN` → `DEFER`
      (and explicitly **not** `NONE`); a crashed read → `ERROR` even with a rebasable state (and not `REBASE`).
- [x] Structural control: the four outcome values are distinct.
