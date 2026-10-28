#!/usr/bin/env python3
"""Refuse the destructive worktree prune for a bot unless the owner said so (issue #794).

`make worktree-prune` deletes directories. Its eligibility test proves a PR merged, but it cannot see
uncommitted work: a worktree mid-flight whose branch tip is already an ancestor of `main` looks
identical to a finished one, and on 2026-10-28 a prune deleted exactly that — the #791 run's worktree
with uncommitted work in it. An unattended bot must therefore never be the thing that runs it.

This is the seam `make worktree-prune` runs before `scripts/worktree_prune.py`:

  * a bot run (`CI` or `BOT` set in the environment) with no `CONFIRM=1` is REFUSED, exit 3, with a
    message naming `make worktree-report` and the re-run spelling;
  * a bot run carrying `CONFIRM=1` proceeds, so an owner who said so is obeyed;
  * the owner's own run (neither `CI` nor `BOT` set) is a no-op, so the documented cleanup path is
    exactly what it was before this guard.

Stdlib only.

Usage:
    python3 scripts/worktree_prune_guard.py          # reads CI / BOT / CONFIRM from the environment
    python3 scripts/worktree_prune_guard.py --dry    # explain the decision, always exit 0
"""
from __future__ import annotations

import argparse
import os
import sys

#: The label every line carries, so the refusal is greppable in a long job log.
TAG = "[worktree-prune]"

#: Exit code for the refusal, distinct from a failed prune (2) in `scripts/worktree_prune.py`.
EXIT_REFUSED = 3

#: Environment values that mean "not set", so `CI=false` does not read as a bot run.
_FALSEY = {"", "0", "false", "no", "off"}

#: The variables whose presence makes this run a bot run.
BOT_VARS = ("CI", "BOT")

#: The variable an owner sets to say "yes, delete".
CONFIRM_VAR = "CONFIRM"

REFUSAL = (
    f"{TAG} REFUSED: worktree-prune deletes directories and cannot see uncommitted work, so an "
    f"unattended bot must not run it (issue #794).",
    f"{TAG} Run `make worktree-report` first — it lists every worktree with merged-into-main, "
    f"open-pr and dirty, and mutates nothing.",
    f"{TAG} When the owner has read that report, re-run with `make worktree-prune CONFIRM=1`.",
)


def bot_run(env: dict[str, str]) -> bool:
    """Is this an unattended/CI run? A set-to-false value does not count."""
    return any(env.get(name, "").strip().lower() not in _FALSEY for name in BOT_VARS)


def confirmed(env: dict[str, str]) -> bool:
    """Did the owner spell out the confirmation?"""
    return env.get(CONFIRM_VAR, "").strip() == "1"


def refusal(env: dict[str, str]) -> str | None:
    """The message to refuse with, or None when the prune may run."""
    if bot_run(env) and not confirmed(env):
        return "\n".join(REFUSAL)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--dry", action="store_true",
                        help="print the decision and exit 0 either way (for a human reading the seam)")
    args = parser.parse_args(argv)

    message = refusal(dict(os.environ))
    if message is None:
        if args.dry:
            print(f"{TAG} guard: allowed (bot={bot_run(dict(os.environ))}, confirm={confirmed(dict(os.environ))})")
        return 0
    print(message, file=sys.stderr)
    return 0 if args.dry else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
