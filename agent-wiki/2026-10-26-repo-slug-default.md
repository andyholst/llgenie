# 2026-10-26 — gh gets the repo slug, not the checkout path

Issues: [#343](https://github.com/asimov-agent/llgenie/issues/343), [#434](https://github.com/asimov-agent/llgenie/issues/434)
OpenSpec: `openspec/changes/repo-slug-default`

## What was wrong

`REPO := $(shell pwd)` is the checkout path (recipes mount it), yet every gh-calling bot target was
written as `--repo $(if $(REPO),$(REPO),asimov-agent/llgenie)` — a fallback that can never apply. `gh`
therefore received an absolute path and refused it:

```
make issue-cleaner-scan
RuntimeError: gh issue list --repo /home/…/worktree-prune … failed:
  expected the "[HOST/]OWNER/REPO" format, got "/home/…/worktree-prune"
```

## What changed

`GH_REPO := $(if $(filter /%,$(REPO)),asimov-agent/llgenie,$(REPO))` — the slug when `REPO` is a path,
an explicit `REPO=owner/name` when it is not — and **all 24** gh-calling sites now use it (9 `$(if …)`
fallbacks plus 15 raw `$(REPO)` arguments that had the same defect).

## Verified live

```
make queued-alarm DRY=1        → [queued-alarm] no job has been queued longer than 30 minutes
make issue-cleaner-scan        → [cleaner] nothing to close (0 tracked remainder(s))
make code-review-scan STATIC=1 → [code-review] no findings: the checks found nothing to file
make issue-cleaner-scan REPO=trending-local-llms/trending-local-llms   → override honoured
```

`tests/test_repo_slug.py` → 4 passed; 3 failed on the pre-change tree.
