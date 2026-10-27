# Tasks — registry-sync-review

- [ ] 1. `scripts/registry_review.py`: `sync_pr()` reads the open `chore/registry-sync` PR and every check bucket (green = non-empty and no `fail`/`pending`/`cancel`).
- [ ] 2. `scripts/registry_review.py`: `selection()` renders the trending list per `(arch, vram, ram)` with each row's first `rank_engines()` server, and reports `slower-than-class` / `no-engine` / `unmeasured` / `empty-tier`.
- [ ] 3. `scripts/registry_review.py`: `brief` writes the precondition + selection table to `registry-review-in.md` and prints `action=review|skip`; `publish` files ONE issue labelled `agent:implement`, keyed by the store's `generated_utc`, linking the store's change issue.
- [ ] 4. `.hermes/skills/registry-sync-review/SKILL.md` — Inputs / Output / Rules, `name` matching the directory; `.hermes/skills/README.md` row.
- [ ] 5. `Makefile`: `registry-review-brief`, `registry-sync-review`, `registry-review-publish` (the leg inside the agent image, redacted transcript, `require_env` first); `.PHONY` and `make help`.
- [ ] 6. `.github/workflows/registry-sync-review.yml`: hourly `:23` + dispatch, owner/collaborator guard, every secret-spending step behind the brief's `review`, redacted transcript upload.
- [ ] 7. `tests/test_registry_review.py`: the selection check (correct list, a wrong order, an unserveable model, an empty tier), the precondition, the brief's `skip`, publish (create / update / link / `clear`), the workflow's gating, and the skill contract.
- [ ] 8. Measured on the real store: `make registry-review-brief` reports `action=skip` with the reason (no open sync PR) and 92 selection findings on `data/models.json` (`nemotron-3.5-lightning-30b-a3b`, no backend).
- [ ] 9. `docs/BOTS.md` (the bot, its slot, the workflow table row) + `agent-wiki/2026-10-27-registry-sync-review.md` and a `CHANGES.md` row naming #709 and the PR.
- [ ] 10. `make test-unit`, `make check-docs`, `make check-wiring`, `make check-agent-skills`, `make check-workflows`, `make lint` green and `make openspec-validate NAME=registry-sync-review` exits 0.
