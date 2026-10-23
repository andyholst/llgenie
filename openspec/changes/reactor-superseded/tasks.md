# Tasks — reactor-superseded

- [x] 1. `scripts/run_failure_reactor.py`: `run_detail()` reads `createdAt` (the run's position in its branch's history).
- [x] 2. `scripts/run_failure_reactor.py`: add `superseded(repo, run, run_id)` — an OPEN PR for a `pull_request` run's head, or a later `success` of the same workflow on the same branch for a `push` run.
- [x] 3. `scripts/run_failure_reactor.py`: `route()` consults `superseded()` on the Route B path only, prints the greppable `SUPERSEDED` line and files nothing.
- [x] 4. `tests/test_run_failure_reactor.py`: a merged-PR run files nothing; a draft-PR run still files; a superseded main push files nothing; an unsuperseded main push still files.
- [x] 5. Close the six measured duplicate issues with the merged-PR / green-main evidence in #565.
- [x] 6. README + `agent-wiki/2026-10-23-reactor-superseded.md` describe the new Route B rule and name #565 / the PR.
- [x] 7. `python3 -m pytest tests/test_run_failure_reactor.py` green, and `make test-unit` green.
- [x] 8. `make openspec-validate NAME=reactor-superseded` exits 0.
