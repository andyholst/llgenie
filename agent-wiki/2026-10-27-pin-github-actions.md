# 2026-10-27 — every GitHub Action runs at a commit, not at a tag

Issue #719 (parent #713). Branch `feat/pin-github-actions`.

## What was verified

- The gate, `make check-actions` (`scripts/pin_actions.py check`): exits **1 on `main`** naming 56
  floating refs, and **0 after the rewrite** — the gate is real, not vacuous.
- The rewrite covers 20 files, 56 refs: `actions/checkout@v4` ×33, `docker/setup-buildx-action@v3`
  ×6, `actions/upload-artifact@v4` ×5, `actions/setup-python@v5` ×5,
  `astral-sh/setup-uv@v6` ×3, `docker/setup-qemu-action@v3` ×2, `actions/setup-node@v4` ×1, plus
  the composite action `.github/actions/docker`.
- `update` is idempotent: a second run prints `nothing to do`.
- `python3 scripts/check_workflows.py check` green — a rewritten `uses:` line still parses.
- `tests/test_pin_actions.py`: 9 passed in the test image (`llgenie/test:latest`).
- Two regressions the pin exposed, both fixed in this change:
  `tests/test_macos_install.py` asserted the literal `docker/setup-buildx-action@v3` (now matched as
  a SHA with an optional tag comment), and `scripts/issue_bot_gates.py` refused the new `ci-unit`
  gate until it was classified `DEFERRED` with its reason (the `FAST_GATES` list is a pinned
  contract of issue #475 and must not widen).

## Decisions

- **The tag stays as a trailing comment.** A bare 40-hex line is unreviewable; the comment is also
  what `update` re-resolves, so freshness is a command rather than a manual scrape.
- **Local refs are exempt.** `./.github/actions/docker` and the reusable workflows are this
  repository's content at the commit being run; pinning them is meaningless.
- **A ref without a `/` is not judged.** `uses: job` appears in this tree as a matrix value; a gate
  that refuses text it cannot classify would be turned off rather than fixed.
- **Renovate does not own Actions.** `renovate.json` (own change, #718) deliberately has no
  `github-actions` manager: an unattended bump must not move an Action without the diff review
  `docs/SECURITY.md` describes.
- **An old pin is not a failure.** `check-actions` fails on floating, never on stale: a stale pin
  still runs reviewed code.

## Status

Implementation complete on the branch; PR open against `asimov-agent/llgenie:main`.
