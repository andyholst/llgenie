## ADDED Requirements

### Requirement: One immutable image per scanner

Each scanner (`trivy`, `grype`+`syft`, `semgrep`) MUST have its own
`containers/scanners/<id>/Dockerfile` whose base image is pinned by digest
(`FROM image@sha256:<64 hex>`) and whose scanner is pinned to an explicit exact version
(`ARG <SCANNER>_VERSION=<version>`). A `FROM` that names a tag without a digest, a version range,
or the literal `latest` MUST fail the gate.

#### Scenario: the shipped images are pinned

Given this repository,
When   `make check-scanner-images` runs,
Then   it exits 0 and names four scanners as digest-pinned and exact-version.

- **Test:** `tests/test_scanner_images.py::test_every_scanner_has_a_pinned_dockerfile`

#### Scenario: a floating base fails

Given a Dockerfile whose `FROM` is `cgr.dev/chainguard/wolfi-base:latest`,
When   the gate reads it,
Then   it exits non-zero, naming the missing digest and the floating tag.

- **Test:** `tests/test_scanner_images.py::test_a_floating_base_fails`

#### Scenario: an unpinned scanner version is loud

Given a Dockerfile with no `ARG <SCANNER>_VERSION=` pin,
When   the gate reads it,
Then   it fails loudly rather than building whatever the base last published.

- **Test:** `tests/test_scanner_images.py::test_an_unpinned_scanner_version_fails`

### Requirement: The published tag names one build of one Dockerfile

`containers/scanners/digests.json` MUST carry, per scanner, the pinned version and a tag equal to
the Dockerfile's content hash. `make scanner-digests` MUST regenerate it, and the gate MUST fail
when it is stale.

#### Scenario: a stale digests file fails

Given a `digests.json` whose `trivy` tag is not the Dockerfile's content hash,
When   `make check-scanner-images` runs,
Then   it exits non-zero, naming the mismatch.

- **Test:** `tests/test_scanner_images.py::test_a_stale_digests_file_fails`

#### Scenario: the tag moves when the Dockerfile changes

Given two Dockerfiles that differ only in the pinned scanner version,
When   each is hashed,
Then   the tags differ, so a bump can never reuse a published tag.

- **Test:** `tests/test_scanner_images.py::test_the_content_hash_moves_with_the_dockerfile`

#### Scenario: write records version and hash

Given a tree with one pinned scanner,
When   `make scanner-digests` runs,
Then   `digests.json` carries that scanner's pinned version and content-hash ref.

- **Test:** `tests/test_scanner_images.py::test_write_records_the_content_hash_and_version`

### Requirement: Each image proves its own version, and CI publishes it

`make test-scanner-image SCANNER=<id>` MUST build the image and require its version command to
print the pinned version. The `scanner-images` CI job MUST build and version-test every scanner on
every run, and MUST publish the content-hash tag on a push run only — the policy living in
`scripts/scanner_image.py`, never in a scenario-scoped workflow `if:`.

#### Scenario: every scanner answers with its pin in CI

Given the `scanner-images` job of `.github/workflows/ci.yml`,
When   it runs `make ci-scanner-images`,
Then   each image is built and its version command prints the version its Dockerfile pins.

- **Test:** CI job `scanner-images` → `make ci-scanner-images` → `python3 scripts/scanner_image.py ci`
  (each `test(<id>)` compares the binary's output with the Dockerfile pin). Locally:
  `make test-scanner-image SCANNER=trivy` — verified on the host for all four images.

#### Scenario: a pull_request run never publishes

Given a run whose `GITHUB_EVENT_NAME` is `pull_request`,
When   `make ci-scanner-images` runs,
Then   every scanner is built and tested and none is pushed.

- **Test:** `python3 scripts/scanner_image.py ci` with `GITHUB_EVENT_NAME=pull_request`
  (CI job `scanner-images` on every PR; the branch prints `build+test only for <id>`).
