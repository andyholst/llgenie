# Tasks — registry-sync-review

- [x] 1. `scripts/registry_review.py`: `sync_pr()` reads the open `chore/registry-sync` PR and every check bucket (green = non-empty and no `fail`/`pending`/`cancel`).
- [x] 2. `scripts/registry_review.py`: `selection()` renders the trending list per `(arch, vram, ram)` with each row's first `rank_engines()` server, and reports `slower-than-class` / `no-engine` / `unmeasured` / `empty-tier`.
- [x] 3. `scripts/registry_review.py`: `brief` writes the precondition + selection table to `registry-review-in.md` and prints `action=review|skip`; `publish` files ONE issue labelled `agent:implement`, keyed by the store's `generated_utc`, linking the store's change issue.
- [x] 4. `.hermes/skills/registry-sync-review/SKILL.md` — Inputs / Output / Rules, `name` matching the directory; `.hermes/skills/README.md` row.
- [x] 5. `Makefile`: `registry-review-brief`, `registry-sync-review`, `registry-review-publish` (the leg inside the agent image, redacted transcript, `require_env` first); `.PHONY` and `make help`.
- [x] 6. `.github/workflows/registry-sync-review.yml`: hourly `:55` + dispatch, owner/collaborator guard, every secret-spending step behind the brief's `review`, redacted transcript upload.
- [x] 7. `tests/test_registry_review.py`: the selection check (correct list, a wrong order, an unserveable model, an empty tier), the precondition, the brief's `skip`, publish (create / update / link / `clear`), the workflow's gating, and the skill contract.
- [x] 8. Measured on the real store: `make registry-review-brief` reports `action=skip` with the reason (no open sync PR) and 92 `no-engine` findings on `data/models.json` over 80 cases, on three models (`nemotron-3.5-lightning-30b-a3b`, `glm-5.3-flash`, `llama-3.1-8b`).
- [x] 9. `docs/BOTS.md` (the bot, its slot, the workflow table row) + `agent-wiki/2026-10-27-registry-sync-review.md` and a `CHANGES.md` row naming #709 and the PR.
- [x] 10. `make loop` green on the final tree (image, download, lint, agents-read, unit `5268 passed, 6 deselected`, install, health, top-tier, top-tier-serve, test, openspec, openspec-tasks, clean), `make check-docs` / `check-wiring` / `check-agent-skills` / `check-workflows` / `check-dispatch-forms` ok, and `make openspec-validate NAME=registry-sync-review` exits 0.
