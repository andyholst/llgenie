# unit-gate-bump-race — proposal

Issue: [#672](https://github.com/asimov-agent/llgenie/issues/672)

## Why

`make test-unit` runs `tests/test_ci_publish_order.py::test_every_image_install_pulls_is_published`,
which resolves the images the **current checkout's** params say `make install` pulls and asks the
real GHCR whether each is published. That is true for `main`, and false for a bump PR: the bump
changes an engine pin, so the tag it resolves has never been published, and it is published only by
the same run's parallel `engine-image-*` job. The gate therefore reds the one thing a bump PR
exists to change.

Measured 2026-10-26 on the open bump PRs:

```
#665 llama.cpp      [install] FAIL llama.cpp/cpu: ghcr.io/asimov-agent/llgenie/llama-cpp:74b104c9-e07a7432-cpu
                    was never published (last registry error: HTTP Error 404: Not Found)
                    FAILED tests/test_ci_publish_order.py::test_every_image_install_pulls_is_published
                    1 failed, 5195 passed, 6 deselected in 2572.39s (0:42:52)

#663 llama.cpp-prism  same test, on linux AND macos (macos: 1 failed, 5195 passed in 4307.56s)
```

The tag is published minutes later by the run itself, and the same lookup then answers `200`
(measured anonymously against GHCR). `unit` needs only `ci-images` in the workflow, so it races
`engine-image` by construction. #169 already fixed this shape for the `install` job by making the
wait a prerequisite of that stage (`make ci-wait-engine-images`, `install_engine_launchers.
install_plan` the single tag list); the unit gate kept its own copy of the assertion and never
received that fix.

## What Changes

- **`tests/test_ci_publish_order.py`** — the real-registry case keeps asserting publication for
  every engine whose committed params are **unchanged** against `origin/main`, and names the ones it
  defers. An engine whose `containers/engines/params/<id>.json` differs from `origin/main` (or has no
  copy there) is the one this run is building: requiring its tag here is the race, and its tag is
  gated where the wait belongs — `make ci-wait-engine-images`, a prerequisite of `ci-install`
  (#169). The exclusion is printed (`[publish-order] … deferred to ci-wait-engine-images: […]`), so
  a reader sees exactly what was not checked and where it is checked instead.
- The change is a scope narrowing of ONE assertion, not a removal: on `main` (where nothing differs
  from `origin/main`) every engine is still checked against the real registry, unchanged.

## Why not the alternatives

- **`pytest.skip`** is forbidden by AGENTS.md, and a skip is not the point: the tags are genuinely
  checked, at the stage that can wait for them.
- **Deleting the case** loses the guard `main` needs — a hand-edited param for an engine nobody
  rebuilt would no longer be noticed by `unit`.
- **Making `unit` wait for the registry** couples a hermetic gate to a 30-minute publish, and would
  still red when the image build fails for an unrelated reason.

## Not covered

- The fork-token case (`make push-engine` denied for an `andyholst:*` head): [#155](https://github.com/asimov-agent/llgenie/issues/155).
- The dependency delta a bump must carry into the image: #186/#192.
