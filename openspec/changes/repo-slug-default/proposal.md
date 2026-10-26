# repo-slug-default — proposal

Issues: [#343](https://github.com/asimov-agent/llgenie/issues/343), [#434](https://github.com/asimov-agent/llgenie/issues/434)

## Why

`REPO := $(shell pwd)` is the **checkout path** — recipes mount it (`-v "$(REPO)":/repo`). Every
gh-calling bot target was written as `--repo $(if $(REPO),$(REPO),asimov-agent/llgenie)`, a fallback
that can never apply, so `gh` received an absolute path and refused it:

```
$ make issue-cleaner-scan
RuntimeError: gh issue list --repo /home/asimov/repository/git/llgenie-wt/worktree-prune --state open …
failed: expected the "[HOST/]OWNER/REPO" format, got "/home/asimov/repository/git/llgenie-wt/worktree-prune"
```

`make queued-alarm`, `make issue-cleaner-apply`, `make code-review-scan`, `make implement-issue`,
`make issue-refiner`, `make issue-dedup`, `make rebase-bot-sweep`, `make architecture-bot-publish`,
`make auto-merge` and others shared the break: 24 recipe sites in total.

## What Changes

- **`GH_REPO := $(if $(filter /%,$(REPO)),asimov-agent/llgenie,$(REPO))`** — the slug: the repo's own
  when `REPO` is a path, a `REPO=owner/name` override when it is not.
- Every `--repo` in the Makefile uses `$(GH_REPO)`; the `$(if $(REPO),…)` fallback is gone.
- `tests/test_repo_slug.py` — no recipe passes the path; the two documented invocations expand to the
  slug; an explicit override still wins; the default resolves to `asimov-agent/llgenie`.

## Benefit

The documented invocation works again — and `REPO=owner/name` keeps its meaning for the operators who
already use it.
