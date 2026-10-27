# syntax=docker/dockerfile:1
#
# Semgrep — SAST over the application code — its own immutable image (issue #714, parent #713).
#
# Why an image and not an install step in the workflow: a scanner installed at scan time is a
# mutable tool on a mutable base, with network access during the scan. This image fixes the base by
# DIGEST and every package by exact version, so the same scan is the same program everywhere.
#
# Kotlin-style rule this file lives by: no floating tag, no version range, no `latest`.
# `make test-scanner-image SCANNER=semgrep` must print the pinned version.

FROM cgr.dev/chainguard/wolfi-base@sha256:0feab531471d2edfcca55f18883441cb7df598e724fa2dedf9985273f532eed7

# Semgrep needs `git` to fetch a rule set pinned by ref, and CA certs for the registry.
ARG SEMGREP_VERSION=1.165.0-r0
RUN apk add --no-cache ca-certificates git "semgrep=${SEMGREP_VERSION}"

USER 65532:65532
WORKDIR /work
ENTRYPOINT ["semgrep"]
CMD ["--version"]
