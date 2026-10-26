# 2026-10-26 — a fork PR's engine publish is a loud skip, not a red job

Issue: [#155](https://github.com/asimov-agent/llgenie/issues/155)
OpenSpec: `openspec/changes/fork-pr-no-publish`
PR: [#675](https://github.com/asimov-agent/llgenie/pull/675)

## What was wrong

`make push-engine` is a step of every `engine-image-*` job. A `pull_request` run's token is scoped to
the BASE repository, so a same-repo head could publish and a FORK head could not — GitHub refuses the
write. Measured on PR #651 (`andyholst:feat/sglang-version-not-pin`, run 40339517705), on a branch
whose build and post-build test had passed:

```
denied: installation not allowed to Write organization package
[engine-image] FAIL push ghcr.io/asimov-agent/llgenie/sglang:35ce3132-5d1a4f11-cuda
make: *** [Makefile:927: push-engine] Error 1
```

So every engine change carried in a fork was permanently red on a permission, never on its code.

## What changed

`scripts/engine_image.py::push` now captures each publish ref's push (printing the registry's own
output), and converts exactly one refusal — the write-permission denial (`WRITE_DENIED`), and only
when `GITHUB_EVENT_NAME=pull_request` — into a skip: a `::warning title=publish skipped::` annotation
naming the ref, the registry and #155, plus a `[engine-image] SKIP publish <ref> …` line, exit 0.
Everything else is untouched: the tag step, the version test before any publish, a denial on a push
run, and any other push failure.

The first attempt put the scope in `ci.yml` as step conditions on the head repository. That was wrong
for this repo: `tests/test_ci_images.py::test_no_ci_step_or_job_is_skipped` exists to keep scenario
decisions out of workflow `if:` blocks, and it caught the attempt (2 failed). The policy moved into
the script, which is also the only place that can observe the registry's actual answer instead of
predicting what the token may do.

## Verified

- `tests/test_ci_publish_scope.py` — 4 passed, driving the real `push()` with a fake runtime; the
  denial fixture is the literal line from run 40339517705.
- Neighbours stay green: `tests/test_engine_skills.py`, `tests/test_ci_images.py`,
  `tests/test_engine_force_rebuild.py`, `tests/test_macos_install.py`,
  `tests/test_engine_build_workflow.py` — 200 passed together.
- `make check-workflows`, `check-wiring`, `check-docs`, `lint`,
  `openspec-validate NAME=fork-pr-no-publish` and the full `make test-unit` are green.
