#!/usr/bin/env python3
"""What each engine cell will ACTUALLY prove when `engine-build` runs it (issue #625).

The sweep's green rows were not equally meaningful — four passed with every flag at exit 1 (the `DEVICE_ONLY`
exemption) and two reported a version that was a log timestamp or `0.0.0` — and the only way to know which was
to read 27 logs. This prints the answer from the COMMITTED params and manifest, before any image is built:

  * `flag-proven`   — the cell's documented flags answer, so the row proves the binary works;
  * `device-exempt` — every flag needs the device, so the row proves only "the file exists + a version-shaped
                      detect"; listed in `DEVICE_ONLY` with its reason and its issue;
  * `disabled`      — not built at all (`DISABLED`, issue #103).

Nothing here builds or pulls: it is a census, and `make engine-gate-report` is how a reviewer sees the
difference between 27 green rows at a glance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import engine_image as ei  # noqa: E402  (the one source of DISABLED / DEVICE_ONLY)


def rows() -> list[dict]:
    """One row per engine x variant the sweep would build, from the committed params + manifest."""
    binaries = json.loads((REPO / "containers" / "engines" / "binaries.json").read_text())["engines"]
    out = []
    for params_file in sorted((REPO / "containers" / "engines" / "params").glob("*.json")):
        params = json.loads(params_file.read_text())
        engine = params["id"]
        for variant, spec in sorted(params["variants"].items()):
            entry = (binaries.get(engine) or {}).get(variant) or {}
            disabled = ei.DISABLED.get((engine, variant), "")
            exempt = ei.DEVICE_ONLY.get((engine, variant), "")
            policy = str(entry.get("probe") or "flags")
            flags = [str(f) for f in (entry.get("flags") or [])]
            if disabled:
                verdict = "disabled"
            elif exempt:
                verdict = "device-exempt"
            else:
                verdict = "flag-proven"
            out.append({"engine": engine, "variant": variant, "verdict": verdict,
                        "policy": policy, "flags": flags, "detect": spec.get("detect", ""),
                        "reason": disabled or exempt})
    return out


def main(argv: list[str] | None = None) -> int:
    table = rows()
    width = max(len(r["engine"]) for r in table) if table else 0
    print(f"[gate-report] {len(table)} cells (engine x variant) from the committed params\n")
    for r in table:
        mark = {"flag-proven": "FLAGS ", "device-exempt": "DEVICE", "disabled": "DISABL"}[r["verdict"]]
        print(f"  {mark}  {r['engine']:<{width}}  {r['variant']:<7} flags={','.join(r['flags']) or '-':<16} "
              f"policy={r['policy']:<6} {('— ' + r['reason']) if r['reason'] else ''}")
    counts = {v: sum(1 for r in table if r["verdict"] == v) for v in ("flag-proven", "device-exempt", "disabled")}
    print(f"\n[gate-report] flag-proven={counts['flag-proven']} device-exempt={counts['device-exempt']} "
          f"disabled={counts['disabled']}")
    print("[gate-report] a device-exempt row proves the FILE plus a version-shaped detect, not that the CLI "
          "runs — it needs a GPU runner to lose the exemption (issue #625)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
