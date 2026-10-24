# Tasks — engine-params-review

- [x] 1. `scripts/engine_params_review.py`: `brief` writes the engine's docs at its pin + current params to `params-review-in.md`.
- [x] 2. `scripts/engine_params_review.py`: `parse_proposals` + `validate` — a proposal is accepted only when its backend is the engine's, the named file exists, the flag's NAME is in it, the quote is a substring, and the flag is not already present.
- [x] 3. `scripts/engine_params_review.py`: `apply_accepted` writes accepted flags into the skill's `cmake_flags.<backend>`, regenerates params/Dockerfiles, writes the PR section; `DRY=1` mutates nothing.
- [x] 4. `.hermes/skills/engine-params-review/SKILL.md` exists and preloads `bot-unattended`; the Makefile leg uses it.
- [x] 5. `Makefile`: the three targets (brief / agent leg through the redaction seam / apply), all `.PHONY`.
- [x] 6. `.github/workflows/engine-bump.yml`: the review runs after the bump and before the PR, non-fatal, and its section lands in the PR body.
- [x] 7. `tests/test_engine_params_review.py`: documented arch flag accepted + applied; uncited, undocumented, wrong-backend and already-present proposals refused; dry run writes nothing; the section reports both sides.
- [x] 8. `.gitignore` + `tests/test_bot_scratch_ignored.py`: the three run inputs are ignored and rostered.
- [x] 9. README + `agent-wiki/2026-10-24-engine-params-review.md` describe the leg and what it may and may not change.
- [x] 10. `make test-unit` green and `make openspec-validate NAME=engine-params-review` exits 0.
