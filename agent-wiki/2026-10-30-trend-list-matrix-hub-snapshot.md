# The trend-list matrix gate is hermetic: `matrix()` replays a recorded Hub snapshot (#1080)

Issue: #1080 — `ci(unit): check-trend-list-matrix is a live-Hub read inside the hermetic ci-unit gate`.
PR: #1109 (`fix/1080-trend-target-hermetic`, base `asimov-agent/llgenie:main`, closes #1080).
Related: #1020 / PR #1077 (the pytest half, `tests/test_trend_list_matrix.py` marked `network`),
#1000/#1002 (the hermetic/networking split), #1067 (a `raw.githubusercontent.com` fetch in the same
gate), #974 (the closed data-path half).

## What was measured (not assumed)

At `origin/main@6d118a03` on this host, `python3 scripts/trend_list_matrix.py --check` exits 0 **after
1655 Hub reads over 117 unique URLs** (recorded by wrapping `_hub_json`): 72 repo trees
(`/api/models/<repo>/tree/main?recursive=true`) and 45 Hub searches (`filter=gguf`, `filter=mlx`,
`author=TensorFold`). Every read is reached from the product function `matrix()`:
`_no_fit_reason()` → `gguf_weights(gguf_repo(model))` → `_tree()` → `_hub_json()`, plus
`mlx_repos()` / `tensorfold_repos()`.

That is the root premise of the issue: the *make* target was a live read even after the *pytest* half
was routed to the network seam, because the live read lives in the product function both halfs call.

## Decision

Option **(b)** of the issue — make the gate hermetic — rather than option (a), move the target to the
live pipeline. The seam already exists in one place: **every** Hub read on this path goes through
`_hub_json`, so one injectable source makes `matrix()` pure. Moving the gate instead would have left
`matrix()` reading the Hub, i.e. left the product function unprovable offline, and left a documented
"hermetic gate" claim false in the other direction.

## What changed

- `scripts/model_engine_pick.py`
  - `HubSnapshotMissing` — a URL the recording does not carry. It is raised, never swallowed:
    `mlx_repos()` / `tensorfold_repos()` re-raise it ahead of their broad `except Exception`, so a gap
    can never read as "this model has no MLX conversions" (which would have produced a *silently*
    different fixture).
  - `hub_snapshot_file(path)` (and `LLGENIE_HUB_SNAPSHOT=<file>`) — replay mode: answers come from the
    recording, **no HTTP request and no Hub disk-cache read or write**, and a missing URL raises. No
    live fallback: a second, differently-implemented path for the same resource is what AGENTS.md
    forbids.
  - `hub_recording()` — records the same compact answers from live reads; recording and replaying are
    refused together. `_TREE_CACHE` is cleared on both transitions because it is keyed by
    `repo@revision` only and must not serve one Hub source from another.
  - The recorded shape is exactly what the consumers read: a tree answer keeps `[[path, size], …]` for
    its *file* entries (dirs and oids are read by nobody: `gguf_weights`, `_snapshot`,
    `plan_download`), a search keeps `[repo id, …]`, and a definite Hub refusal (the 404 on the empty
    repo `gguf_repo()` can hand back) keeps `{"error": {"status": 404}}` so replay answers as the Hub
    did. 117 answers: **232 KB recorded vs 18.9 MB of raw envelopes.**
  - Default behaviour is byte-identical for live use: with neither set, `_hub_json` is the same read
    it was (disk cache, shared transient budget, definitive status on first answer).
- `scripts/trend_list_matrix.py` — `--check` replays `tests/fixtures/hub-snapshot.json` by default;
  `--check --live` (make: `LIVE=1`) keeps the old live comparison; the render path records the
  snapshot **in the same run** that rewrites the fixture, so the two can never describe different Hub
  answers.
- `tests/fixtures/hub-snapshot.json` — the recording (new).
- `tests/test_hub_snapshot.py` — new module (PR #1077's lane owns
  `tests/test_trend_list_matrix.py` / `tests/test_check_model_links.py`, so the pin lives here):
  the gate rebuilds the committed matrix with `urllib.request.urlopen` replaced by a raiser; a
  poisoned Hub disk cache is ignored by replay; a missing URL raises naming the URL; the MLX and
  TensorFold searches propagate the gap; the default path still reads a real (local) HTTP server; a
  recording round-trips and replay/record are exclusive.

## Verification (real output)

- `env HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 ALL_PROXY=… NO_PROXY= python3 scripts/trend_list_matrix.py --check`
  → `[trend-list-matrix] OK tests/fixtures/trend-list-matrix.json (81 cases, recorded
  tests/fixtures/hub-snapshot.json)`, exit 0. The same command at `main` stalled (exit 124).
- `git diff --stat tests/fixtures/trend-list-matrix.json` after the live render = empty: the recording
  reproduces the committed fixture byte-identically, and the live render still produces it.
- `tests/test_hub_snapshot.py`: 6 passed. The whole-matrix case is 33 s (the matrix build itself), the
  rest are sub-second.

## Left open

Nothing in this change's scope. #1020's pytest file keeps its `network` mark: it compares live, and
this seam is what a hermetic version of it could use later — that routing is that lane's decision.
