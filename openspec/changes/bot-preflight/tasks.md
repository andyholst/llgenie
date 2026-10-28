# Tasks

- [x] 1. `openspec/changes/bot-preflight` — proposal + `specs/bot-preflight/spec.md` (G/W/T, a `- **Test:**` line per scenario) + this checklist, written before any code
- [x] 2. `scripts/bot_preflight.py` — stdlib only: fetch `origin/main`, refuse a non-`asimov-agent/llgenie` GitHub origin, refuse a dirty tree, `--ff-only` a behind tree, refuse a diverged one with the left/right counts, write `preflight.txt` (`AGENTS:` line + heading digest + main + tree state + profile), `--check` prints the first difference; every refusal exits 2 and names what it read
- [x] 3. `tests/test_bot_preflight.py` — real scratch git repositories (a local bare remote, real fetch / ff / diverge): at-main, ahead, behind, dirty, diverged, wrong origin, unreachable remote, heading digest, stale `--check`, gitignored record, Makefile + docs wiring
- [x] 4. `Makefile` — `bot-preflight` target with a `##` help line, declared in `.PHONY:`, forwarding `PROFILE=` / `CHECK=` / `REMOTE=` / `BRANCH=`
- [x] 5. `scripts/check_pr_hygiene.py` — the `AGENTS:` rule (missing line, sha ≠ `git merge-base origin/main HEAD`, counts ≠ `AGENTS.md` at that sha), body read from `--pr-body-file` / `$PR_BODY_FILE` / `$GITHUB_EVENT_PATH` / explicit `PR=`+`REPO=` via `gh`, no body on a push to `main` = a note not a failure
- [x] 6. `tests/test_pr_hygiene.py` — one test per rejection case (missing, wrong sha, wrong counts, event-body source, no-body, unreadable body file) with real git merge-bases
- [x] 7. `.hermes/skills/bot-unattended/SKILL.md` states the preflight and `scripts/check_agent_skills.py` fails when it is gone; `tests/test_agent_skills.py` pins both directions
- [x] 8. `.hermes/skills/issue-implement/SKILL.md` requires the `AGENTS:` line in `pr-body.md`
- [x] 9. `.gitignore` — `preflight.txt` as a bot run input (its own section: it is not `.md`, so the `.md` roster in `tests/test_bot_scratch_ignored.py` is untouched)
- [x] 10. Workflows — `issue-bot.yml` and `architecture-bot.yml` call `make bot-preflight` where they synced `main`; `fix-bot.yml` calls it after `make bot-sync-branch`
- [x] 11. `docs/BOTS.md` — the target, the record it writes, the `AGENTS:` line a PR body carries, and the legs that call it
- [x] 12. `agent-wiki/2026-10-28-bot-preflight.md` + one `CHANGES.md` row, naming issue #792 and the PR
- [x] 13. The `AGENTS.md` section this change could not write (protected file, the unattended run is refused) is filed as its own linked issue — #849
- [x] 14. Verified against real output: `make bot-preflight PROFILE=implementer` and `make bot-preflight CHECK=1` pass on a clean worktree of this branch (`AGENTS: 17cdcf36f97e2a7897cde09c4e190cf21e71ac4e 87255b 1302l`); `make check-pr-hygiene`, `make check-agent-skills`, `make check-wiring`, `make check-docs`, `make check-workflows`, `make lint` and `make openspec-validate NAME=bot-preflight` all exit 0; `tests/test_bot_preflight.py tests/test_pr_hygiene.py tests/test_agent_skills.py` → 57 passed inside `llgenie/test`. The full `make test-unit` suite is `ci-unit`'s stage.
