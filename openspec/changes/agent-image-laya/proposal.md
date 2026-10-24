# Install the agent image without an extra it never uses

## Why

The agent (Hermes) image cannot be built, so every bot job is down: `agent-jev-preflight` is the
first step of `issue-bot`, `issue-refiner`, `issue-dedupe`, `fix-bot`, `rebase-bot` and
`code-review-bot`, and it builds the image when the commit's tag is not on GHCR.

Measured (run `40099608144`, job `120888884874`, 2026-10-24):

```
#12 14.37   ✗ Resolving Python dependencies failed; last 7 lines of output:
#12 14.37       error: No solution found when resolving dependencies for split
                            (markers: python_full_version == '3.14.*' and sys_platform == 'android')
#12 14.37         cause: Because torch>=2.0.0 has no `python_full_version >= '3.14'`-compatible
                            wheels and laya==0.3.3 depends on torch>=2.0.0, we can conclude that
                            laya==0.3.3 cannot be used.
#12 14.50 ✗ Plugin 'nerve' conflicts with the dependencies pinned by Hermes core or an enabled
            plugin, so it was not admitted. Resolver: uv lock exited 1
[nerve-ci] nerve is not enabled in /root/.hermes
```

`scripts/install_nerve_ci.sh` calls `hermes plugins install … --yes-deps --enable`. Hermes then takes
a **universal** `uv lock` for the plugin's workspace — every marker split, not just the image's. The
plugin (`keeltrace/hermes-nerve` @ `3de7d949`) declares `laya = ["laya==0.3.3"]` as an **optional
extra**, laya requires `torch>=2.0.0`, and torch publishes no wheels for `python_full_version >=
'3.14'` or `sys_platform == 'android'` — so the lock has no solution and the plugin is never admitted.

The extra is dead weight in this image, on two independent grounds: the bots run the plugin's
default `reflex_backend` (`jev`) and this script writes no `reflex_backend`, so the Laya sidecar
backend is never selected; and the plugin imports laya **lazily**, inside a function
(`hermes_nerve/reflex/laya_service.py:126`), so an install without the extra still imports and
serves jev.

An added `[tool.uv] environments` block in the plugin's `pyproject.toml` does **not** fix it —
measured in a real container against the same pinned ref: Hermes generates its own workspace and
does not inherit the plugin's `[tool.uv]` (the identical `uv lock exited 1` comes back).

## What changes

`scripts/install_nerve_ci.sh` installs the plugin in three explicit steps instead of one:

1. `hermes plugins install "$PLUGIN" --ref "$REF" --no-deps` — clone and record provenance, resolve
   nothing;
2. drop the `laya` extra from the **installed** copy's `pyproject.toml`, asserting it was there (a
   plugin that stops declaring it fails the build with a pointer to this issue, rather than
   resolving extras blind);
3. `hermes plugins enable nerve` — which resolves the now-satisfiable graph.

Every existing proof is unchanged and still runs afterwards: the bundle is at
`${HERMES_HOME}/plugins/nerve/plugin.yaml`, `hermes plugins list --json` reports
`enabled … pinned@<sha8>`, `hermes_nerve.profiles` imports and the `lean` sidecar reads back through
the plugin's own loader, every `plugins.entries.nerve.settings.*` value equals what the script wrote,
`gate_mode` stays the quoted string, and no provider token is in the image. The gate stays **hard**:
a plugin that cannot be admitted still fails the build, because a bot running without its decision
layer is the defect #238 exists to prevent.

## Impact

- `scripts/install_nerve_ci.sh` — the install/enable pair above; no other step changes.
- `tests/fixtures/fake-hermes/hermes` — the stand-in CLI learns `plugins enable`, and its
  `plugins install` writes a `pyproject.toml` carrying the same `laya` extra the pinned plugin does,
  so the drop step is exercised against a real file.
- `tests/test_agent_nerve.py` — three new assertions: the install call carries `--no-deps` and never
  `--yes-deps`; the extra is gone from the installed `pyproject.toml` and the plugin is enabled;
  the drop step fails loudly when the extra cannot be found.
- `README.md`, `agent-wiki/` — the image's documented wiring, which currently says one `--yes-deps`
  call.

Not in this change: the upstream `keeltrace/hermes-nerve` fix (marker the `laya` extra, or add
`[tool.uv] environments`), the missing CI build of the agent image (#586), and the image hash not
covering the Hermes version (#406).
