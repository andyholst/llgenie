# 2026-10-27 — the security stack names no scanner this repository does not ship

Issues #714, #715. Landed in `main` as `82c0220` (PR #729, which carried the stack) and
`7bd7771` (PR #725, the scanner images). PRs #727 and #728 were closed as superseded by #729.

## What was verified

- **The tree names no scanner the repository does not run.** `git grep -i` for the retired
  fourth scanner on `origin/main` after `35e9658` returns **0 files** — no Dockerfile, workflow,
  `digests.json` entry, doc, OpenSpec change, test, agent-wiki entry or Makefile line.
- **The roster is three images and four tool ids**: `containers/scanners/{trivy,grype,semgrep}/`,
  with `syft` reached through the Grype image (`--entrypoint syft`) so the SBOM writer needs no
  image of its own. `make check-scanner-images` and `make check-security-scan` exit 0 on
  `origin/main`.
- **The unknown-tool test refuses an id that is in no roster** (`gitleaks`), so the refusal is not
  pinned to a vendor name that a later change could quietly make real.
  `tests/test_security_scan.py::test_an_unknown_tool_is_refused` passes in `make test-unit`
  (4814 passed, 6 deselected on the stacked branch).
- **The whole stack needs no credential**: nothing reads a scanner token, so no scan is skipped for
  a missing key — the property `docs/SCANS.md` and `docs/SCANNERS.md` now state.

## Decisions

- **A scanner the repository does not run is not a scanner the repository documents.** The remaining
  sentences were narrative ("a fourth scanner was removed …"), not configuration, but a reader
  consulting `docs/SCANNERS.md`, the OpenSpec proposal or the agent-wiki would have concluded the
  pipeline runs four scanners and that one needs a paid account. Each is rewritten to state the rule
  that holds: every scanner is a pinned apk package, so a scan is reproducible from its Dockerfile
  alone.
- **Trivy is the primary scanner**; Syft/Grype supply the SBOM match, Semgrep the SAST pass. Nothing
  in the roster, `digests.json`, the workflow or the Makefile changed to make this true — only the
  documents that still described a fourth one.
- **A superseded stacked PR is closed with evidence, not left conflicting.** #729 carried #727's and
  #728's commits, so their content is on `main`; re-rebasing them onto `82c0220` showed their diff
  was strictly behind it (it would have reverted `check()`'s SBOM guard). Closing them with the
  verification output keeps the tracker honest about where the work shipped.

## Status

Merged. The scanner images are published by `main`'s run; the scan, the issue filer and the
remediation bot are on `main` and gated by `check-security-{scan,issues,bot}` inside `ci-unit`.

## Related

- `agent-wiki/2026-10-27-scanner-images.md` — the images themselves (#714).
- `agent-wiki/2026-10-27-security-scan-workflow.md` — the scan seam and its policy (#715).
- `docs/SCANNERS.md`, `docs/SCANS.md` — what a reader consults for the current roster.
