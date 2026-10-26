# sglang-version-not-pin — proposal

Issue: [#636](https://github.com/asimov-agent/llgenie/issues/636) (duplicate of the same failure: [#650](https://github.com/asimov-agent/llgenie/issues/650))

## Why

`make test-built-engine` runs every installed `llgenie-engine-*` start script with `--version` and
requires a version back. `sglang/rocm` answered `installed sglang pin 35ce31329305`, so the stage
failed on a published image that is perfectly healthy:

```
[test-built-engine] FAIL llgenie-engine-sglang --version: [engine-runner] sglang/rocm: installed sglang pin 35ce31329305
make: *** [Makefile:262: test-built-engine] Error 1
```

The cause is the skill's `detect`: when the installed distribution reports `0.0.0` (the ROCm wheel
does), it fell back to the **commit sha** (`pin {pinned_short}`). A sha is not a version — it has no
dots, and the repo's own rule (#625) is that a version must be a version.

## What Changes

- `skills/engines/sglang/SKILL.md` — the `0.0.0` fallback becomes the **pinned version** (`{version}`,
  i.e. `0.5.22`), not the sha; params regenerated.
- `tests/test_engine_skills_pipefail.py` — a case that fails when any skill's `detect` prints
  `{pinned_short}` as its version.

## Benefit

The published-image stage stops failing on a healthy engine, and the version an operator reads is the
one the engine was built at.
