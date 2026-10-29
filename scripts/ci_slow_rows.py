#!/usr/bin/env python3
"""Which heavy matrix rows this CI run schedules (issue #859).

`linux / top-tier` downloads and serves a REAL model on every pull request. What it proves — that
this host can fetch a model and answer on the OpenAI API through the engine image — is a property
of `main` and of the weekly engine/registry data, not of an arbitrary diff, and it is one of the
longest rows in the matrix. Measured on #767's run 40694228407 (a ONE-FILE docs PR): 26 jobs
success, 1 skipped, 0 failed, and the run stayed open ~2h on one heavy row alone.

The macOS half of issue #859 was resolved by deletion, not by a condition: `ci.yml` has no `macos`
group any more (`#870`), so `macos / unit` and `macos / top-tier` simply do not exist. What is left
is the row above.

So `linux / top-tier` is **not scheduled on a pull request** and **is scheduled everywhere else** —
`push` to `main` (one run per merge still catches a model/engine regression), a dispatch, any
non-PR event. A PR that really needs it adds the `ci:slow` label and the next run of that PR
schedules it. Every other row is untouched: `linux / unit` stays the PR gate for the suite.

The decision lives here, in one place with a CLI, instead of inline in `ci.yml`: a value that makes
a job run or not run can only be tested while it is Python. `make ci-slow-rows` calls this script
from `ci.yml`'s `guard` job and publishes the key below as a job output; the `linux` caller passes
it into `pipeline.yml`, whose `top-tier` job uses it as its single matrix axis. A row that is not
scheduled is the `["none"]` placeholder row: it runs no make target, it runs on no runner of its own
(`runs-on` keeps it on `ubuntu-latest`), and its one unguarded step prints why.

Fail closed: anything that is not a `pull_request` (an unknown event, an empty event) schedules the
row. The only way to lose it is a pull request without the label.

Usage:
    python3 scripts/ci_slow_rows.py decide --event pull_request --labels '["bug"]'
    python3 scripts/ci_slow_rows.py decide --event push          # scheduled
"""
from __future__ import annotations

import argparse
import json
import os
import sys

#: The label a PR carries to ask for the heavy rows (documented in `docs/BOTS.md`).
SLOW_LABEL = "ci:slow"

#: The matrix rows a scheduled job runs. `["none"]` is the placeholder: one row, no make target.
RUN = '["run"]'
NONE = '["none"]'


def _labels(raw: str) -> list[str]:
    """The PR's label names from a JSON array (what `toJSON(github.event…labels.*.name)` emits),
    a comma/space separated list, or `null`/blank when the run is not a pull request."""
    text = (raw or "").strip()
    if not text or text == "null":
        return []
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return [part for part in text.replace(",", " ").split() if part]
    if loaded is None:
        return []
    if isinstance(loaded, str):
        return _labels(loaded)
    return [str(name) for name in loaded]


def decide(event: str, labels: list[str]) -> dict[str, str]:
    """The `$GITHUB_OUTPUT` values for one run.

    `linux / unit` has no row axis at all — it is the PR gate for the suite and always runs — so
    the only value here is the heavy row's.
    """
    is_pr = (event or "").strip() == "pull_request"
    slow = (not is_pr) or (SLOW_LABEL in labels)
    return {
        "slow": "true" if slow else "false",
        "top_tier_rows": RUN if slow else NONE,
    }


def say(event: str, labels: list[str], values: dict[str, str]) -> str:
    """The one legible line the run log carries, so an absent row is a stated decision."""
    state = "run" if values["top_tier_rows"] == RUN else "absent"
    return (f"[ci-slow-rows] event={event or '(none)'} labels={','.join(labels) or '-'} "
            f"slow={values['slow']} linux/top-tier={state}"
            + ("" if values["slow"] == "true"
               else f" (a pull request schedules it only with the `{SLOW_LABEL}` label, "
                    f"issue #859)"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ci_slow_rows", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decide", help="print the row selection as $GITHUB_OUTPUT lines")
    d.add_argument("--event", default=os.environ.get("EVENT", ""),
                   help="github.event_name of this run")
    d.add_argument("--labels", default=os.environ.get("LABELS", ""),
                   help="the PR's label names (JSON array, or comma separated)")
    args = ap.parse_args(argv)

    labels = _labels(args.labels)
    values = decide(args.event, labels)
    print(say(args.event, labels, values))

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            for key, value in values.items():
                fh.write(f"{key}={value}\n")
    else:
        for key, value in values.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
