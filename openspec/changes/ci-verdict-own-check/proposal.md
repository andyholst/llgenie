# ci-verdict-own-check — Proposal

Issue: [#1837](https://github.com/asimov-agent/llgenie/issues/1837) — the verdicted `engine-build` branch was
green but the verdict gate reddened it forever.

## Why

The `ci-verdict` step POSTs its answer as a `ci-verdict` check-run on the judged run's head (#1864). GitHub
lists that posted row BACK as a job of the very run being judged — measured 2026-11-06 on run 42275871131
(head `cf88d28`): 10 real jobs all green plus an 11th `ci-verdict => failure wf=CI` row returned by
`GET /actions/runs/<id>/jobs`. `ci_scope.verify()` counts any observed row not in the scope table that reports
`failure` as an unaccounted failure, so every re-judge re-counted the judge's own one-off `failure` from an
earlier stale pass and stayed red forever (a self-referential loop blocking #1837).

## Change

The judge strips its own posted `ci-verdict` row from the job set it judges before calling `verify()`. The
accounting rule "an unknown REAL failing job is a red" stays intact; only the verdict's own output is removed.

## Benefit

A green run with a verdict answers green instead of reading its own echo as a permanent failure; #1837
unblocks.
