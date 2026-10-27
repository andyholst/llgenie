# 2026-10-27 — one immutable Wolfi image per scanner

Issue #714 (parent #713). Branch `feat/scanner-images`.

## What was verified

- **All four images were built and each printed its pinned version** (`make test-scanner-image`
  equivalent, on this host):

  | Scanner | Base | Pin | Built |
  |---|---|---|---|
  | trivy | `cgr.dev/chainguard/wolfi-base@sha256:0feab531…` | `0.70.0-r5` | 402 MB |
  | grype (+syft) | same base | `grype 0.121.0-r0`, `syft 1.55.0-r1` | 290 MB |
  | semgrep | same base | `1.165.0-r0` | built |
  | snyk | same base | `1.1308.3` + sha256-verified release asset | built |

- Every scanner is a **Wolfi apk package** except Snyk, whose CLI is fetched from the
  version-named GitHub release and checked against the release's published sha256 — Wolfi does not
  package it, and an unverified download would be the mutable tool this image exists to prevent.
- `make check-scanner-images` → 0 (`4 scanner image(s) pinned by digest, exact version, and
  matching digests.json`), and 1 when a fixture floats its base or its `digests.json` is stale.
- `tests/test_scanner_images.py`: 7 passed.
- Two defects the real builds exposed, both fixed in this change: wolfi-base has no
  `/usr/local/bin`, so the Snyk image now creates it before `curl -o` (without it the download
  fails with `curl: (23) client returned ERROR on write`), and the gate's floating-`FROM` rule
  initially matched the digest form itself (a negative lookahead keeps `image@sha256:<hex>` out).

## Decisions

- **Digest-pinned base, exact apk version, content-hash tag.** A tag is a moving pointer inside
  Chainguard's registry; an apk range compiles to a different scanner next build; the published
  tag is the Dockerfile's sha256 prefix, so one tag can never mean two builds (the `llgenie/test`
  convention).
- **Grype and Syft share an image.** A Grype run against a different Syft's SBOM is a different
  result, so the pair is pinned and shipped together.
- **The publish policy lives in the script**, not in a workflow `if:` — a scenario-scoped
  condition in YAML is how a publish silently stops happening (AGENTS.md). `ci` publishes on a
  push run and prints `build+test only` on a `pull_request`.
- **`digests.json` is generated, not hand-edited**, and the gate fails when it disagrees with a
  Dockerfile: a stale entry points the scan workflow at a build that no longer matches the tree.
- **A bump commits the Dockerfile and `digests.json` together** (`docs/SCANNERS.md`).

## Status

Implementation complete on the branch; PR open against `asimov-agent/llgenie:main`.
