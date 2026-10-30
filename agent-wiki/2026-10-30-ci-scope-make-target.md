# ci-scope make target: the classifier through `make`, the workflow through the guard

`scope.yml` selects the CI classes a diff needs (issue #824). Two repo rules it previously missed
are now enforced:

1. **One make target per step.** The `scope` job's classify step used to run
   `python3 scripts/ci_scope.py` inline. The standing rule (#270/#296/#305) is that a workflow step
   which runs a repo script must route through `make`, keeping only gh/git orchestration inline. The
   new `make ci-scope BASE="…"` (module + `.PHONY`, mirroring `ci-slow-rows`) owns the classifier and
   the step calls it.

2. **The owner/collaborator guard.** `scope.yml` is dispatchable (`workflow_dispatch:`) but carried no
   actor guard, unlike every other dispatchable workflow (#295). It now has the exact shared guard job
   (byte-identical body) that the `scope` job `needs`, the same shape `ci.yml` uses.

**The renovate reconciliation (issue #718, #824, #904):** `check_renovate` flags a `pull_request`
path filter only when it could exclude a build/dependency file. #904's `paths-ignore` is docs-only
(`docs/**`, `agent-wiki/**`, `openspec/**`, `README.md`, `CHANGES.md`) — it contains no
`containers/**`, Dockerfile, `tools/` or `scripts/` glob, so a docs-only PR skipping ci.yml provably
cannot skip an image build. A positive `paths:` allowlist, or a `paths-ignore` that names a build
stem, is still refused.
