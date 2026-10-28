# Evidence probe: a docs-only diff (issue #824)

This file exists only to produce a pull request whose diff is **entirely** in the `docs` class, so
the trigger selection can be observed instead of trusted: `ci.yml` carries
`pull_request.paths-ignore` for `docs/**` (plus `agent-wiki/**`, `openspec/**`, `README.md` and
`CHANGES.md`), and `docs.yml` carries the same list under `paths:`.

Measured on this PR: the jobs GitHub actually queues, the `scope` check's printed classes, and the
`docs` job's gate list. The PR is not meant to merge; it is closed once the run ids are recorded in
the #824 review.

No code, no make target, no index change: the only gate this diff can move is the markdown lint and
the documentation index, which is exactly the set `docs.yml` runs.
