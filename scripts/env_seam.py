"""llgenie's own environment seams, under llgenie's name (#251).

Several knobs that belong to llgenie — not to any inference server — carried a
`LLAMA_*` name, which reads as a llama.cpp flag and misleads exactly the people
the rename is for. Each seam now has an `LLGENIE_*` name that wins, while the old
`LLAMA_*` name keeps working as a deprecated alias so no host, script or CI job
breaks on the rename.

Names that genuinely belong to llama.cpp (`LLAMA_SERVER`, `LLAMA_SERVER_TREE`,
`LLAMA_CUBLAS`, `LLAMA_HOST`) are NOT routed through here: they are upstream's.
"""
from __future__ import annotations

import os

# The deprecated-alias pairs, so a test can walk them instead of trusting prose.
SEAMS = {
    "LLGENIE_MODELS_ROOT": "LLAMA_MODELS_ROOT",
    "LLGENIE_BACKEND": "LLAMA_BACKEND",
    "LLGENIE_RAM_BYTES": "LLAMA_RAM_BYTES",
    "LLGENIE_SPEC_DRAFT_P_MIN": "LLAMA_SPEC_DRAFT_P_MIN",
    "LLGENIE_HEADROOM_BYTES": "LLAMA_HEADROOM_BYTES",
}


def env_seam(new: str, old: str, env=None, default=None):
    """Value of an llgenie seam: `new` if set and non-empty, else `old`, else `default`.

    `env` defaults to `os.environ`; pass a dict in tests (or in code that already
    carries an env snapshot) to keep the lookup hermetic.
    """
    env = os.environ if env is None else env
    for name in (new, old):
        val = env.get(name)
        if val is not None and str(val).strip() != "":
            return val
    return default


def seam(new_or_old: str, env=None, default=None):
    """`env_seam` for a name given in either form — new wins, old is accepted."""
    for new, old in SEAMS.items():
        if new_or_old in (new, old):
            return env_seam(new, old, env, default)
    raise KeyError(f"{new_or_old!r} is not an llgenie seam (see SEAMS)")
