# fork-pr-no-publish — proposal

Issue: [#155](https://github.com/asimov-agent/llgenie/issues/155)

## Why

`make push-engine` is a step of every `engine-image-*` job, and a `pull_request` run carries a token
scoped to the BASE repository. A same-repo head can write this repository's packages; a FORK head
cannot, and GitHub refuses the write outright. So every fork PR that moves an engine tag arrived red
on `engine-image-<engine>-<variant>` — on a branch whose build and post-build test both passed.

Measured on PR #651 (`andyholst:feat/sglang-version-not-pin`, run 40339517705, 2026-10-26), both
engine-image jobs:

```
ae8a69caad45: Waiting
denied: installation not allowed to Write organization package
[engine-image] FAIL push ghcr.io/asimov-agent/llgenie/sglang:35ce3132-5d1a4f11-cuda
make: *** [Makefile:927: push-engine] Error 1                              # job 121639543085
                                                                          # rocm: …, 871de137-rocm
```

The same branch's linux jobs were green (`unit` fixed in #636's follow-up), and the images were
built and tested successfully — only the publish was refused, by a permission GitHub will never
grant a fork PR. `make push-engine` cannot be made to succeed there; the job can only stop asking.

#155 already named this as its remaining scope: "a fork PR that moves an engine tag leaves its
install jobs green — or skips them with a named reason — and no PR run ever writes the moving
`:<arch>` tag."

## What Changes

- **`scripts/engine_image.py::push`** — each publish ref's push is captured, and a refusal that is
  the write-permission denial (`denied: installation not allowed to Write organization package`, plus
  the other registry spellings in `WRITE_DENIED`) **inside a `pull_request` run only** becomes a
  skip: a `::warning::` annotation (`title=publish skipped`, naming the ref, the registry and #155)
  plus a `[engine-image] SKIP publish <ref> …` log line, exit 0. Everything else is unchanged: the
  tag step, the version test that runs before any publish, and every other push failure still fail
  loudly.
- **`AGENTS.md`** (engine pipeline rule 3) and **`README.md`** state the mechanism instead of the old
  "must fail loudly" sentence, which described a write that can never succeed.
- **`tests/test_ci_publish_scope.py`** — drives the real `push()` with a fake runtime: the PR-#651
  denial inside a `pull_request` run is a skip; the same denial on a push run still fails; an
  unrelated `pull_request` failure still fails; a successful publish is untouched.

## Why the policy is in the script, not in a workflow `if:`

`tests/test_ci_images.py::test_no_ci_step_or_job_is_skipped` requires every step condition in
`ci.yml`/`pipeline.yml`/`published.yml` to be one of a small set (a `none`-placeholder skip, an OS
guard, `always()`). A scenario-scoped `if:` is exactly the leak that guard exists to prevent, and the
repo's rule is that such decisions live in make/scripts — one code path, testable on the host. The
script also owns the one fact that matters: the registry's own refusal, so the skip is based on what
happened rather than on a prediction of what the token can do.

## Why not the alternatives

- **Leaving it red** (today's behaviour) makes every engine change from a fork permanently unmergeable
  by CI, and the red says "denied: Write organization package" — a permission, not a defect.
- **`continue-on-error: true`** would hide a genuine publish failure on a push run, which is the one
  place publishing must fail loudly.
- **A workflow `if:` on the head repository** is a scenario-scoped step condition, which the guard
  above rejects (and it would predict the token's rights instead of observing them).
- **Having the fork's own Actions publish to the fork's registry** produces images nothing installs:
  `LLGENIE_REGISTRY` is this org.

## Not covered

- The unit gate's own race with the same parallel publish: [#672](https://github.com/asimov-agent/llgenie/issues/672).
- Publishing a fork PR's images at all (a first-class "publish from an untrusted head" design) is not
  proposed here; the run that lands the change on `main` publishes them.
