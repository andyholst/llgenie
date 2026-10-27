# Scans — Trivy, Syft, Grype and Semgrep from their pinned images

The scan pipeline is `.github/workflows/security-scan.yml`; every scanner it runs comes from
[`docs/SCANNERS.md`](SCANNERS.md)'s immutable image, and the one place a scanner is invoked is
`scripts/security_scan.py`. There is no second code path: the workflow, a developer and CI call the
same `make` targets.

## Triggers

| Event | When | Failure policy |
|---|---|---|
| `pull_request` (main) | every PR | **report-only** — `pr_fail_on` is empty, so a PR is never gated by a pre-existing advisory |
| `push` (main) | every merge | `full` mode — `fail_on` (critical + high, with a fix) |
| `schedule` | daily 04:23 UTC | `full` mode |
| `workflow_dispatch` | owner, repository bot, collaborator with write | the `enforce` input, default `full` |

The manual form asks two things: `tools` (`all` or one scanner) and `enforce` (`full` or `pr`). The
`guard` job runs **before any scanner** and allows the owner, `github-actions[bot]` on a same-repo
head, and any collaborator with `admin`/`maintain`/`write`; anyone else is refused.

## Why a PR run is narrower than the daily run

A repository accumulates High advisories with a fix that no one has applied yet. If a PR enforced
`fail_on`, every PR — including one that fixes something else — would be red, which is how a
security gate gets switched off. So a `pull_request` run enforces `pr_fail_on` (critical only,
with a fix) and still uploads every report; the daily and manual runs enforce the full policy. Both
sets live in `data/security-policy.json`, never in a workflow literal.

```json
{"fail_on": ["critical", "high"], "pr_fail_on": [],
 "require_fix": true, "issue_severities": ["critical", "high"]}
```

`pr_fail_on` is **empty on purpose**: any repository eventually carries a High with a fix nobody has
applied yet, and gating every PR on it reds PRs that fix something else — the standard way a security
gate gets switched off. A PR run therefore *reports* (SARIF + the artifact) and files nothing; the
daily schedule and a manual dispatch enforce `fail_on` and file the issues. Set `pr_fail_on` to a
subset of `fail_on` when the tree is clean enough to gate PRs on it.

`require_fix: true` means an advisory with no fixed version is **recorded, never blocking** — it is
work nobody can do today, and #716 decides which recorded findings become issues.

## Where the scanner image comes from

The run uses the ref `containers/scanners/digests.json` names. It is **pulled** when it is published.
A `pull_request` run before the first publish — and any run whose token cannot read the packages —
does not skip the scan: the **same Dockerfile** the publish job builds (digest-pinned base, exact
versions) is built locally and tagged with the ref the run asked for, and the log says which path was
taken. A build that fails fails the run, loudly; there is no third path and no silent skip.

Every scanner runs as the **invoking user** (`docker run --user <uid>:<gid>`): the mounted checkout
belongs to the runner, so without it trivy cannot create its report (`permission denied`) and the run
would leave root-owned files in the tree (issue #433).

## Outputs

- **CycloneDX SBOM** — `security-reports/sbom.cdx.json`, written by Syft from the Grype image;
  uploaded as the `security-reports` artifact (30-day retention) together with every scanner report.
- **SARIF** — `security-reports/trivy.sarif`, uploaded to the Security tab with
  `github/codeql-action/upload-sarif` (pinned by SHA), category `trivy`.
- **Reports** — `security-reports/sbom.cdx.json`, `trivy.json`, `grype.json`, `semgrep.json`.
- **No scanner takes a secret.** Trivy, Syft, Grype and Semgrep run from their pinned images, so
  no scan is ever skipped for a missing credential (Snyk, removed, was the exception).

## Targets

| Target | What it does |
|---|---|
| `make sbom` | Syft → `security-reports/sbom.cdx.json` |
| `make security-scan TOOL=<id>` | one scanner from its pinned image (Grype needs `make sbom` first) |
| `make security-scan-all` | Syft SBOM, then Trivy, Grype, Semgrep |
| `make security-verdict MODE=full\|pr` | apply the policy to the reports; the run's exit code |
| `make check-security-scan` | **The gate** (inside `make ci-unit`): empty/unknown policy severities, `pr_fail_on ⊄ fail_on`, or a scanner missing from `digests.json` fails |

## Findings become tagged issues

`make security-issues` (after the verdict, on a `push`, a `schedule` run and a manual dispatch —
never on a `pull_request`, whose findings belong to the PR) turns the reports into GitHub issues:

- **one issue per (advisory, package)**, keyed by an HTML marker in the body
  (`<!-- security-finding: trivy:CVE-…:numpy -->`), so a re-scan **updates** the same issue and
  never opens a duplicate;
- **labels**: `security`, `vulnerability`, `severity:critical` / `severity:high`,
  `component:python` / `component:container` / `component:code`, and `auto-fixable` when the
  scanner names a fixed version — every label is created (with colour and description) on first use;
- **body**: advisory id and scanner, affected package, current → fixed, severity, the run link,
  the suggested action, and a `Not covered` section;
- **clearing**: an advisory the scanner no longer reports is commented with the run that cleared it
  and closed; a closure that `gh` refuses (a remediation PR still references it) is a warning, never
  a crash.

`make security-issues-plan` prints the same create/update/clear plan and mutates nothing.

| Target | What it does |
|---|---|
| `make security-issues-plan` | print the plan (no GitHub write) |
| `make security-issues SLUG=owner/name RUN_URL=<link>` | create/update/close through `gh` |
| `make check-security-issues` | **The gate** (inside `make ci-unit`): `issue_severities` empty or not a subset of `fail_on`, a missing label, or a marker that does not round-trip fails |

## The remediation bot

`.github/workflows/security-bot.yml` runs `make security-bot`, which is `scripts/security_bot.py`:

1. **select** the oldest open issue carrying `security` + `vulnerability` + `auto-fixable`;
2. **parse** the package and `current -> fixed` out of the body the issuer wrote (#716) — a body
   without those lines is refused, never guessed;
3. **edit the one line that owns the pin** (`tools/requirements.in` / `requirements-dev.in`). A
   compiled `requirements*.txt` is never an edit target — it is regenerated;
4. **run the fast gates** (`make lint check-wiring check-docs check-security-scan`);
5. **push a branch and open ONE PR** whose body carries `Issue: / Fix: / Benefit: / Technical:` and
   `closes #<issue>`.

**Green or nothing:** when a gate is red the bot reverts the edit, comments the real output on the
issue, and opens no PR. It never merges, never pushes to `main`, never force-pushes.

It **refuses** a finding it cannot place — a `component:container` advisory (a base-image or
scanner bump, which is a reviewed change) or a package pinned nowhere it can see — and says so on
the issue instead of guessing.

| Target | What it does |
|---|---|
| `make security-bot-pick` | print the one issue the run would take |
| `make security-bot DRY=1` | print the edit, push nothing |
| `make security-bot` | apply, run the gates, push, open the PR |
| `make check-security-bot` | **The gate** (inside `make ci-unit`): the select labels must exist in the issuer's roster and no compiled file may be an edit target |

## Reading a failure

`make security-verdict` prints every blocking finding as
`<source>: <advisory> <package> <current> -> <fixed> (<severity>)`. That line is exactly what
`make security-issues` (#716) turns into a tagged issue with the `security`, `vulnerability`,
`severity:*`, `component:*` and `auto-fixable` labels.
