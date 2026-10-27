# 2026-10-27 — the scans run from pinned images, and a PR run is narrower than the daily run

Issue #715 (parent #713, blocked by #714). Branch `feat/security-scan-workflow`, cut from
`feat/scanner-images` because the scan reads `containers/scanners/digests.json`.

## What was verified

- `python3 scripts/security_scan.py check` → `OK: fail_on=['critical','high'] pr_fail_on=['critical']
  require_fix=True, 4 pinned scanner refs`.
- `tests/test_security_scan.py` → 9 passed (trivy/grype normalisation, full vs pr policy, no-fix
  never blocks, verdict exit codes, corrupt report refuses, real policy sane, workflow shape).
- `make check-dispatch-forms` → OK on 16 dispatchable workflows (the new `security-scan.yml` has a
  self-describing form and the `docs/BOTS.md` table is regenerated).
- `make check-wiring` → OK, 239 targets, CI reaches 93; `check-workflows` green (every `${{ }}` in
  the new file parses); `check-docs` green after `docs/SCANS.md` was linked from `README.md`.

- **Five defects the real CI runs found, each fixed and re-verified here** (the local suite could not
  see any of them, because they only appear when the scanners actually run):
  1. `denied` pulling `llgenie/trivy:<hash>` — the image is published on a push to `main` only, so a
     PR run has no tag. `ensure_image()` now pulls when published and otherwise builds the SAME
     Dockerfile and tags it with the same ref (three tests: pull / build / loud failure).
  2. the SARIF step failed on a file that no run had produced — it is now gated on `hashFiles`.
  3. trivy could not write its report (`permission denied`): the image's USER is non-root while the
     mounted checkout belongs to the runner. `_run` passes `--user <uid>:<gid>` (also satisfies
     issue #433).
  4. `syft` never ran: the Grype image's ENTRYPOINT is `grype`, so `syft …` was read as a second
     positional ("accepts at most 1 arg(s), received 2"). The SBOM step uses `--entrypoint syft`.
  5. Semgrep refused `--config auto` with metrics off; the SAST step pins `--config=p/default`.
- A `pull_request` run is **report-only** (`pr_fail_on: []`), measured locally: 27 findings recorded,
  verdict `REPORT-ONLY (pr)` exit 0, while `MODE=full` exits 1 listing the critical/high findings that
  have a fix.

- **Snyk is opt-in, not part of a scan.** It is the one scanner here that needs a paid account, a
  token and a third-party service to receive the analysis; Trivy + Syft/Grype + Semgrep cover the
  same question with data the runner downloads itself. So `TOOLS` is the local three,
  `OPTIONAL_TOOLS` is `snyk`, and `make security-scan TOOL=snyk` is the deliberate way to run it.

## Decisions

- **One seam.** `scripts/security_scan.py` is the only place a scanner is invoked; the workflow,
  a developer and CI call the same `make` targets. A second inlined scanner command is the defect.
- **`pr_fail_on` exists.** Enforcing `fail_on` (critical+high) on every PR would red every PR as
  soon as one High with a fix is outstanding — the standard way a security gate gets switched off.
  A `pull_request` run enforces critical only; the daily schedule and a manual dispatch enforce the
  full policy. Both are data in `data/security-policy.json`, not literals in a workflow step.
- **`require_fix: true`.** An advisory with no fixed version is recorded and never blocks: it is
  work nobody can do today, and #716 decides which recorded findings become issues.
- **A skipped scanner is loud.** Without `SNYK_TOKEN` the Snyk step prints `SKIP … not treated as a
  pass` and writes the reason into `security-reports/snyk.json`.
- **A corrupt report fails.** `findings()` raises instead of answering zero — a green run that read
  nothing is the failure mode this avoids.
- **Trivy is invoked twice** (JSON for the verdict, SARIF for the Security tab) because it takes one
  `--format` per run; both runs scan the same tree with the same flags.
- **SBOM retention is 30 days** as an artifact; the CycloneDX file is also in the reports directory,
  so #716 can read component versions from it.

## Status

Implementation complete on the branch; the PR opens once #714 (`feat/scanner-images`) merges, since
the scan cannot run without `containers/scanners/digests.json` on `main`.
