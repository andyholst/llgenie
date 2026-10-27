# security-bot — tasks

- [x] 1. `scripts/security_bot.py` — select / parse / apply_plan / apply / check
- [x] 2. Selection: oldest open issue carrying security+vulnerability+auto-fixable (deterministic, no random pick)
- [x] 3. Parsing from the issuer's body format; a body without the package/version lines is refused, never guessed
- [x] 4. The edit targets only `tools/requirements*.in`; a compiled `requirements*.txt` is never an edit target
- [x] 5. Green or nothing: the fast gates run before the push; a red gate reverts the edit, comments the real output, opens no PR
- [x] 6. Refusals: a container advisory and an unpinned package are commented, not guessed
- [x] 7. The PR body carries Issue/Fix/Benefit/Technical and `closes #<issue>`; the commit is authored `Asimov Agent <support@docondee.com>`
- [x] 8. `.github/workflows/security-bot.yml` — issues[labeled] / schedule / workflow_dispatch, the guard job first, scoped permissions; the dispatch table regenerated
- [x] 9. Make targets `security-bot-pick`, `security-bot` (DRY=1), `check-security-bot`; `.PHONY`, gate in `ci-unit`, classified in `scripts/issue_bot_gates.py`
- [x] 10. `tests/test_security_bot.py` (11 tests, real git + real file edit + recording `gh`) passing; `docs/SCANS.md` documents the bot; `check-docs` / `check-wiring` / `check-dispatch-forms` / `check-workflows` green
