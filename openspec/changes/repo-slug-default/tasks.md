# Tasks

- [x] 1. `openspec/changes/repo-slug-default` — proposal + spec (G/W/T, a `- **Test:**` line per scenario) + this checklist, written before the code (issues #343/#434)
- [x] 2. `Makefile` — `GH_REPO` defined next to `REPO`; all 24 gh-calling sites use it (9 `$(if …)` fallbacks + 15 raw `$(REPO)`)
- [x] 3. `tests/test_repo_slug.py` — no path form, documented invocations carry the slug, an override wins, the default is a slug
- [x] 4. Verified live: `make queued-alarm DRY=1`, `make issue-cleaner-scan`, `make code-review-scan STATIC=1` all answer; RED on the pre-change tree (3 failed)
- [x] 5. `agent-wiki/2026-10-26-repo-slug-default.md` records it
