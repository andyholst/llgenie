---
name: trend-list-matrix-hub-snapshot
about: the trend-list matrix gate replays a recorded Hub snapshot, so matrix() is pure on the vendored registry
status: active
---

# The trend-list matrix gate is hermetic: matrix() replays a recorded Hub snapshot (issue #1080)

## Proposal

`make ci-unit` runs `make check-trend-list-matrix`, which runs
`python3 scripts/trend_list_matrix.py --check`. That script builds the whole 81-case matrix with
`mp.matrix(registry, vram, ram, arch)` and compares it to `tests/fixtures/trend-list-matrix.json`.
`matrix()` is not a function of the vendored registry alone: for every model no engine can run it
calls `_no_fit_reason()` → `gguf_weights(gguf_repo(model))` → `_tree(repo)` → a Hub GET of
`https://huggingface.co/api/models/<repo>/tree/main?recursive=true`, `gguf_repo()` runs a Hub search,
and `mlx_repos()`/`tensorfold_repos()` run two more. Measured at `origin/main@6d118a03` on this host:
`--check` exits 0 with a route after 1655 Hub reads (117 unique URLs), and stalls (exit 124 under a
300 s bound through an unroutable proxy) with none.

So the gate's verdict depends on the Hub's answer of the hour: a 429, a DNS blip or a tree upstream
reshaped reds `linux / unit` on a PR that never touched the matrix — and a red there cannot be told
apart from a genuine drift in the committed list.

## Motivation

The #1000/#1002 split removed the pytest half of this (PR #1077 marks the live comparison
`network`), but the make half was untouched: `ci-unit` still reaches the Hub. The remaining live
path is the **product** function `matrix()`, which is why fixing the tests alone does not fix the
gate.

The seam that does fix it is a recording of the Hub answers the matrix consumed, replayed instead of
fetched. Every Hub read in this path goes through one function, `_hub_json`, so one injectable
source makes the whole product path pure: `matrix()`, and with it `trend_rows()`, become functions of
the vendored registry plus the recording, and the committed fixture is reproducible with no route.

## Change

- `scripts/model_engine_pick.py` — the injectable source, in `_hub_json` (the ONE Hub entry point):
  - `HubSnapshotMissing` (a URL the recording does not carry) is loud, and `mlx_repos()` /
    `tensorfold_repos()` re-raise it ahead of their broad `except Exception` rather than turning a gap
    in the recording into "this model has no conversions".
  - `hub_snapshot_file(path)` (context manager) and `LLGENIE_HUB_SNAPSHOT=<file>` (env) put `_hub_json`
    in replay mode: answers come from the recording, **no HTTP and no Hub disk cache**, and a missing
    URL raises `HubSnapshotMissing`. There is no live fallback — a second, differently-implemented
    path for the same resource is what this repo forbids.
  - `hub_recording()` (context manager) collects the same compact answers from live reads; recording
    and replay are mutually exclusive and say so.
  - Default behaviour is unchanged: with neither set, `_hub_json` is the live read it always was.
  - The recorded shape is exactly what the consumers read — a tree answer is `[[path, size], …]`
    (file entries only), a search answer is `[repo id, …]` — so the recording is ~184 KB where the
    raw answers are 18.9 MB.
- `scripts/trend_list_matrix.py` — `--check` replays `tests/fixtures/hub-snapshot.json` by default
  (`--live` keeps the old live comparison), and the render path records the snapshot and writes it in
  the same run that rewrites the fixture, so the two can never describe different Hub answers.
- `tests/fixtures/hub-snapshot.json` — the recording behind the committed fixture (new file).
- `tests/test_hub_snapshot.py` — a NEW module (not `tests/test_trend_list_matrix.py` or
  `tests/test_check_model_links.py`, which PR #1077's lane owns) that pins: the gate reproduces the
  fixture with every HTTP entry point replaced by a raiser; a URL missing from the recording is a loud
  `HubSnapshotMissing` and never a live call; the default live path still goes through `_hub_open`
  against a local HTTP server; and a recording round-trips.
- Docs: `docs/ARCHITECTURE.md` no longer calls the gate a live read; `agent-wiki/` note +
  `docs/changes.d/` fragment.

## Acceptance

- [ ] `python3 scripts/trend_list_matrix.py --check` exits 0 with the HTTP path replaced by a raiser
      and reproduces `tests/fixtures/trend-list-matrix.json` byte-identically (`git diff --stat` empty).
- [ ] With a route, `--check --live` still exits 0, and the render path still writes both files.
- [ ] Negative control: pointing the gate back at the live read reds the offline test, and the
      unroutable-proxy run of `--check` exits 0 only because of the recording.
- [ ] A URL absent from the recording raises `HubSnapshotMissing`, including through `mlx_repos()`.
- [ ] `make check-trend-list-matrix`, `make test-unit` (which runs `ci-unit`'s targets), `make lint`,
      `make check-docs`, `make check-wiring` and `make openspec-validate NAME=trend-list-matrix-hub-snapshot`
      exit 0.
