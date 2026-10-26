# 2026-10-26 — sglang's version fallback was a commit sha

Issue: [#636](https://github.com/asimov-agent/llgenie/issues/636), duplicate [#650](https://github.com/asimov-agent/llgenie/issues/650)
OpenSpec: `openspec/changes/sglang-version-not-pin`

## What was wrong

`test-published-sglang-rocm` failed on `main` (run 40276061217) with an image that pulled and verified
fine:

```
[engine-image] pulled published ghcr.io/asimov-agent/llgenie/sglang:35ce3132-9eceeb86-rocm (sha256:3fcd5656…), same digest as …:rocm
[test-built-engine] FAIL llgenie-engine-sglang --version: [engine-runner] sglang/rocm: installed sglang pin 35ce31329305
```

`sglang`'s `detect` falls back when the distribution reports `0.0.0` (the ROCm wheel does) — and the
fallback was the commit sha. A sha has no dots, so the built-engine stage rightly rejected it: a
version must be a version (#625).

## What changed

- `skills/engines/sglang/SKILL.md`: the fallback is the pinned version (`{version}` → `0.5.22`).
  Params regenerated (`containers/engines/params/sglang.json`).
- `tests/test_engine_skills_pipefail.py`: fails when any skill's `detect` prints `{pinned_short}`.

## Verified

- In the published rocm image (`ghcr.io/asimov-agent/llgenie/sglang:35ce3132-9eceeb86-rocm`), the fixed
  detect prints `sglang 0.5.22`.
- `tests/test_engine_skills.py` + `tests/test_engine_skills_pipefail.py` → 97 passed.
- `make check-engine-params` → 0 stale.

## Status

Fix + guard on a branch off `main`; the PR closes #636 and #650 (same failure, filed twice by the
reactor).
