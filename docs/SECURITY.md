# Security — supply chain

This page is the reference for what this repository pins, how it is updated, and which gate
keeps it true. It is linked from [`README.md`](../README.md).

## GitHub Actions are pinned to a commit, never a tag

A tag lives in someone else's repository and moves without a commit here: `actions/checkout@v4`
runs whatever `v4` points at when the job starts, so a force-pushed or compromised release
changes what this repository executes. Every `uses:` in `.github/workflows/**` and
`.github/actions/**` is therefore a full 40-character commit SHA, with the tag kept as a
trailing comment so the line is still readable in review:

```yaml
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
```

Two kinds of reference are exempt, because they cannot move independently of the commit being
run: this repository's own composite actions and reusable workflows (`./.github/actions/docker`,
`./.github/workflows/pipeline.yml`).

### The gate

| Target | What it does |
|---|---|
| `make check-actions` | **Fails** on any non-local action ref that is not a full commit SHA. Part of `make ci-unit`, so a floating ref cannot merge. |
| `make actions-report` | Prints every `uses:` ref the gate reads — pin state, `file:line`, and the tag. |
| `make update-actions` | Re-resolves every pinned ref's tag to its current commit and rewrites the workflows in place. Needs `gh` (or `GITHUB_TOKEN`) and network. |

`scripts/pin_actions.py` is stdlib-only for `check` and `report`, so the gate runs on the host
exactly as CI runs it, on Linux and macOS alike. Only `update` reaches the network.

### Updating a pinned action

1. `make update-actions` — every `# vN` comment is re-resolved to the commit it now points at,
   and the SHA is rewritten. An already-current tree is byte-identical, so a second run is a
   no-op.
2. Read the diff: the tag comment is what makes it reviewable (`# v4` → `# v4` with a new SHA is
   a moved tag; `# v4` → `# v5` is a version bump and needs its release notes read).
3. `make check-actions && make check-workflows` — the pin gate and the workflow-expression gate
   (a rewritten `uses:` line must still parse).
4. Commit the result with the reason — this is the only place an Action's pin changes.

Renovate does **not** own these pins: `renovate.json` deliberately carries no
`github-actions` manager, so an unattended bump cannot move an Action without a review of this
diff. Adding that manager later is a separate decision, not an accident.

### A pin that is behind is not a broken pin

`make check-actions` fails on a *floating* ref, never on an *old* one. A pinned SHA that is
several releases behind still runs exactly the code that was reviewed, which is the property the
gate exists to protect; freshness is `make update-actions`' job, and it is a deliberate,
reviewed act.
