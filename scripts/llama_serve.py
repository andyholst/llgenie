"""Deprecated alias for `scripts/llgenie_serve.py` (renamed in #251).

The CLI serves every engine in the registry — 24 of them — so it is named after
the project rather than after one of the servers it can start. This file stays
for one release so an existing script, cron entry or habitual invocation that
references the old path keeps working: importing it hands back the real module
(same objects, same identities), and running it runs the CLI.

Import `llgenie_serve` instead; this shim is removed in a follow-up.
"""
from __future__ import annotations

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_module = importlib.import_module("llgenie_serve")

if __name__ != "__main__":
    # `import scripts.llama_serve` (or `from llama_serve import x`) must hand back
    # the real module, so every attribute and function identity matches.
    sys.modules[__name__] = _module
else:
    sys.exit(_module.main())
