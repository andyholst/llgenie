# pin-github-actions — proposal

Issue: [#719](https://github.com/asimov-agent/llgenie/issues/719)
Parent: [#713](https://github.com/asimov-agent/llgenie/issues/713)

## Why

Every third-party GitHub Action in this repository floats on a mutable tag. A tag is a pointer
inside someone else's repository: it moves without a commit here, so a force-pushed or
compromised release changes what this repository executes. Measured on `main` at `2cbfb11`:

```
$ grep -rhoE 'uses: [^ ]+' .github/workflows/*.yml | sort | uniq -c | sort -rn
     33 uses: actions/checkout@v4
      6 uses: docker/setup-buildx-action@v3
      5 uses: actions/upload-artifact@v4
      5 uses: actions/setup-python@v5
      3 uses: astral-sh/setup-uv@v6
      2 uses: docker/setup-qemu-action@v3
      1 uses: actions/setup-node@v4
```

56 third-party refs across 20 files, none pinned. Nothing in the repository checks this, so a new
floating ref merges silently.

## What Changes

- **Pin every third-party ref to a full commit SHA**, keeping the tag as a trailing comment
  (`uses: actions/checkout@11d5960a… # v4`) so the line stays reviewable.
- **`scripts/pin_actions.py`** — one seam with three commands: `check` (the gate), `report` (what
  it reads), `update` (re-resolve each pinned tag to its current commit; idempotent).
- **`make check-actions` / `make actions-report` / `make update-actions`**, with `check-actions`
  in `make ci-unit` so a floating ref cannot merge.
- **`docs/SECURITY.md`** — the pinning rule, the three targets, and the documented update
  process, linked from `README.md`.
- **`tests/test_pin_actions.py`** — each rule proven on a fixture tree, then the real tree
  asserted fully pinned.

Local references (`./.github/actions/docker`, `./.github/workflows/pipeline.yml`) and non-action
`uses:` values (a matrix value) are exempt: they cannot move independently of the commit, or they
are not action refs at all.

## Not covered

- Container image references in Dockerfiles — the scanner images are pinned by digest in their own
  change (#714), and a general Dockerfile digest gate is not this change.
- Renovate's `github-actions` manager: making the update path a command rather than an unattended
  bot is the deliberate choice here (see `docs/SECURITY.md`).
