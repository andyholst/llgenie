#!/usr/bin/env python3
"""Refuse the destructive worktree prune for a bot unless the owner said so (issue #794).

`make worktree-prune` deletes directories. Its eligibility test proves a PR merged, but it cannot see
uncommitted work: a worktree mid-flight whose branch tip is already an ancestor of `main` looks
identical to a finished one, and on 2026-10-28 a prune deleted exactly that — the #791 run's worktree
with uncommitted work in it. An unattended bot must therefore never be the thing that runs it.

This is the seam `make worktree-prune` runs before `scripts/worktree_prune.py`:

  * an unattended run with no `CONFIRM=1` is REFUSED, exit 3, with a message naming the marker that
    said "unattended", `make worktree-report`, and the re-run spelling;
  * an unattended run carrying `CONFIRM=1` proceeds, so an owner who said so is obeyed;
  * the owner's own shell (no marker set) is a no-op, so the documented cleanup path is exactly what
    it was before this guard.

"Unattended" has to be true for every lane a bot actually takes, or the gate is inert (issue #794's
first review: keying on `CI`/`BOT` alone never fired, because neither reaches a bot). The three lanes
and the marker each one carries:

  * a GitHub workflow step  -> `CI=true`, set by GitHub itself;
  * a leg INSIDE the agent image -> `BOT=1`, forwarded by the Makefile's `AGENT_BOT_MARKER` on every
    `docker run` that boots the agent image (`docker run` does not inherit the host environment, and
    the image sets no such `ENV`, so this is the only way the container's `make` can see it);
  * a host-dispatched lane (the Kanban dispatcher spawns the agent on the host) -> the dispatcher's
    own `HERMES_KANBAN_TASK` / `HERMES_KANBAN_WORKSPACE` / `HERMES_KANBAN_BRANCH` /
    `HERMES_KANBAN_WORKSPACES_ROOT`.

Stdlib only.

Usage:
    python3 scripts/worktree_prune_guard.py          # reads the markers / CONFIRM from the environment
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

#: The variables whose presence makes this run unattended. Every lane a bot takes must appear here —
#: a marker a leg cannot actually receive is a gate that never fires.
BOT_VARS = (
    "CI",                            # a GitHub workflow step (GitHub sets it in every step)
    "BOT",                           # a leg inside the agent image (Makefile AGENT_BOT_MARKER)
    "HERMES_KANBAN_TASK",            # a host-dispatched (Kanban) lane
    "HERMES_KANBAN_WORKSPACE",
    "HERMES_KANBAN_BRANCH",
    "HERMES_KANBAN_WORKSPACES_ROOT",
)

#: The variable an owner sets to say "yes, delete".
CONFIRM_VAR = "CONFIRM"

REFUSAL = (
    f"{TAG} REFUSED: worktree-prune deletes directories and cannot see uncommitted work, so an "
    f"unattended bot must not run it (issue #794).",
    f"{TAG} Run `make worktree-report` first — it lists every worktree with merged-into-main, "
    f"open-pr and dirty, and mutates nothing.",
    f"{TAG} When the owner has read that report, re-run with `make worktree-prune CONFIRM=1`.",
)


def bot_markers(env: dict[str, str]) -> list[str]:
    """The variables that make this run unattended, in BOT_VARS order. A set-to-false value does not count."""
    return [name for name in BOT_VARS
            if env.get(name, "").strip().lower() not in _FALSEY]


def bot_run(env: dict[str, str]) -> bool:
    """Is this an unattended/CI run? A set-to-false value does not count."""
    return bool(bot_markers(env))


def confirmed(env: dict[str, str]) -> bool:
    """Did the owner spell out the confirmation?"""
    return env.get(CONFIRM_VAR, "").strip() == "1"


def refusal(env: dict[str, str]) -> str | None:
    """The message to refuse with, or None when the prune may run."""
    markers = bot_markers(env)
    if markers and not confirmed(env):
        return "\n".join((REFUSAL[0].replace("unattended bot", f"unattended bot (marker: {' '.join(markers)})"),) + REFUSAL[1:])
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--dry", action="store_true",
                        help="print the decision and exit 0 either way (for a human reading the seam)")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    message = refusal(env)
    if message is None:
        if args.dry:
            print(f"{TAG} guard: allowed (markers={','.join(bot_markers(env)) or 'none'}, "
                  f"confirm={confirmed(env)})")
        return 0
    print(message, file=sys.stderr)
    return 0 if args.dry else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
