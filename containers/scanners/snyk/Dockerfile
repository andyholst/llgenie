# syntax=docker/dockerfile:1
#
# Snyk CLI — the pinned upstream binary, verified against its published sha256 — its own immutable image (issue #714, parent #713).
#
# Why an image and not an install step in the workflow: a scanner installed at scan time is a
# mutable tool on a mutable base, with network access during the scan. This image fixes the base by
# DIGEST and every package by exact version, so the same scan is the same program everywhere.
#
# Kotlin-style rule this file lives by: no floating tag, no version range, no `latest`.
# `make test-scanner-image SCANNER=snyk` must print the pinned version.

FROM cgr.dev/chainguard/wolfi-base@sha256:0feab531471d2edfcca55f18883441cb7df598e724fa2dedf9985273f532eed7

# Wolfi does not package the Snyk CLI, so it is fetched from the release the version names and
# VERIFIED against the digest published for that release. A checksum that does not match fails the
# build; an unpinned download would be exactly the mutable tool this image exists to prevent.
ARG SNYK_VERSION=1.1308.3
ARG SNYK_SHA256=5f323f45885341ea1473639859271925912ece82a2f77bc146bb4468f9838840
RUN apk add --no-cache ca-certificates curl \
 && mkdir -p /usr/local/bin \
 && curl -fsSL -o /usr/local/bin/snyk \
      "https://github.com/snyk/cli/releases/download/v${SNYK_VERSION}/snyk-linux" \
 && echo "${SNYK_SHA256}  /usr/local/bin/snyk" | sha256sum -c - \
 && chmod 0755 /usr/local/bin/snyk \
 && snyk --version

USER 65532:65532
WORKDIR /work
ENTRYPOINT ["snyk"]
CMD ["--version"]
