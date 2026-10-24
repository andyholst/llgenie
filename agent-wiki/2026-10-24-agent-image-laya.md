# 2026-10-24 — the agent image installs without an extra it never uses (#585)

Issue: **#585** (implemented here). Filed from the same audit and **not** implemented in this change:
**#586** (no CI job builds the agent image on a PR or push, so a hash-moving PR merges green and every
bot then rebuilds it inline). Already open: **#406** (the image hash covers the Dockerfile and scripts
but not the Hermes version it installs). **#584** is the reactor's tracker for the same failed run and
was closed as a duplicate of #585. PR: this branch's PR against `asimov-agent/llgenie:main`.

## What was measured

Run `40099608144` / job `120888884874`, step *Prove the JEV engine is active* — the first step of every
bot job. The agent image was not published for its tag (`agent:2e2c6363bb32`), so the job built it and
the build died:

```
#12 14.37   ✗ Resolving Python dependencies failed; last 7 lines of output:
#12 14.37       error: No solution found when resolving dependencies for split
                            (markers: python_full_version == '3.14.*' and sys_platform == 'android')
#12 14.37         cause: Because torch>=2.0.0 has no `python_full_version >= '3.14'`-compatible wheels
                            and laya==0.3.3 depends on torch>=2.0.0 …
#12 14.50 ✗ Plugin 'nerve' conflicts with the dependencies pinned by Hermes core … uv lock exited 1
[nerve-ci] nerve is not enabled in /root/.hermes
```

`install_nerve_ci.sh` called `hermes plugins install … --yes-deps --enable`. `--yes-deps` makes Hermes
take a **universal** `uv lock` over the plugin's workspace; the plugin's optional `laya` extra pulls
`torch`, and torch has no wheels for the py3.14 / android marker split, so the lock has no solution and
the plugin is never admitted.

## The decision

Install in three explicit steps and scope the extras to what this image uses:

1. `hermes plugins install "$PLUGIN" --ref "$REF" --no-deps` — clone + provenance, resolve nothing.
2. Drop the `laya` extra from the **installed** `pyproject.toml`, asserting it was there (a pin that
   stops declaring it fails the build and points at #585).
3. `hermes plugins enable nerve` — resolves a graph that now has a solution.

Why dropping the extra is correct and not a workaround: the bots run the plugin's default
`reflex_backend` (`jev`) and the script writes no `reflex_backend`, so the Laya sidecar backend is
never selected; and the plugin imports laya **lazily**, inside a function
(`hermes_nerve/reflex/laya_service.py:126`), so an install without the extra still imports and serves
jev.

Why not `[tool.uv] environments`: **measured, not assumed.** Appending
`environments = ["python_full_version < '3.14'", "sys_platform != 'android'"]` to the installed
plugin's pyproject was tried first in a real container against the same pin — Hermes generates its own
workspace and does not inherit it, and the identical `uv lock exited 1` came back. Dropping the extra
was the only one of the two that enabled the plugin.

The gate stays hard: the bundle file, `enabled … pinned@<sha8>`, the profile sidecar read back through
the plugin's own loader, every `plugins.entries.nerve.settings.*` value and the absence of a token are
all still assertions that fail the build.

## Verification

- `tests/test_agent_nerve.py` — 34 pass in the CI test image. Four new tests: the install call carries
  `--no-deps` and never `--yes-deps` (read from the argv the stand-in CLI actually received, via a new
  invocation log), the extra is gone while the other extras survive, the removal step fails loudly on a
  pyproject without the extra, and it edits only the optional-dependencies table (a `laya =` line in
  `[project]` is left alone).
- Proven against the base: with `origin/main`'s `install_nerve_ci.sh` and fake CLI swapped in, **all
  four** new tests fail and the other 30 pass — the asymmetry a real fix has.
- A **real image build**: `python3 scripts/ci_images.py ensure agent` on this host, which runs the
  script in the same Dockerfile the bots use.

## Status

The bot never merges; CI's `auto-merge` owns landing. #586 (a CI job that builds this image on a
PR/push, and publishing on merge) is the structural follow-up that stops a latent rot like this one
from surfacing as a fleet-wide outage.
