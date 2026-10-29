# 2026-10-28 — the rebase lane's behaviour joins the tree

**Issue:** [#873](https://github.com/asimov-agent/llgenie/issues/873) — put tonight's fleet rules into every
llgenie bot's `SOUL.md`, by issue and PR, never by a private edit.
**Home:** `agents/<profile>/` (issue #791, PR #834).
**PR:** this branch, stacked on `feat/agents-profile-tree` because `agents/` is not on `main` yet.

## What this change does

`agents/llgenie-pr-merge-conflict/SOUL.md` is the rebase lane's behaviour, reviewable and diffable. It carries:

- the **fleet block from #873 verbatim**, under its own heading, so a diff across profiles shows the same text;
- the lane's own four rules, which the canonical block cannot express: **one rebaser at a time** (degrade to
  alert-only once the in-repo sweep is green again, and never escalate a rejected lease to a bare `--force`),
  **conflicts resolved as unions with every file named**, **staleness measured and published before any branch
  moves** (`git merge-base --is-ancestor <tip> origin/main`, the empty list a valid result), and **verdicts read
  from `check-runs` conclusions** — `cancelled` means *not yet*, never red, which `gh pr checks`' fail column
  reports as if it were;
- `never-merge`, stated in the exact form the manifest declares, so `make check-agent-profiles` proves it.

`agents/manifest.json` gains the profile with `"rules": ["never-merge"]`.

## One test changed, and why

`tests/test_agent_profiles.py::test_manifest_lists_both_host_profiles` asserted
`names == ["llgenie-planner", "llgenie-issse-implementer"]` — an equality that makes **every** later SOUL PR red
for doing exactly what #873 asks: adding a profile. Measured today: #875 and #877 both fail this assertion with
their own `agents/<profile>/SOUL.md` in place, so the gate was blocking the change it exists to support.

It now asserts the two original profiles are **present** (subset, plus the orchestrator's two standing rules),
which keeps the property that mattered — "the live host profiles are listed" — without vetoing additions. The
relaxation is named here rather than slipped in.

## Verified

- `python3 scripts/check_agent_profiles.py check` → `OK: 3 host-agent profile(s), each with a SOUL.md stating the
  rules its manifest declares; every skill's frontmatter name matches its directory and carries no secret value`
- `pytest tests/test_agent_profiles.py` in the `llgenie/test` container (parent repo mounted, which the worktree
  requires) → **19 passed**
- `make check-docs` → ok, and this note is indexed in `CHANGES.md`

## Not covered

- The move of this profile's *skills* under `agents/` — #873 scopes that out to one paragraph of pointer.
- #875 and #877: they still fail the equality assertion on their own branches; this PR removes the cause, so they
  need a rebase onto it rather than a fix of their own.
- Syncing this tree into the live `~/.hermes/profiles/llgenie-pr-merge-conflict/` — `make sync-agent-profile` is
  the seam and it is the owner's call to run it.
