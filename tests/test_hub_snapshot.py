"""The trend-list matrix gate replays a recorded Hub snapshot (issue #1080).

`scripts/trend_list_matrix.py --check` used to be a live Hugging Face read dressed as a hermetic
check: `matrix()` asks the Hub for a repo's real GGUF/MLX file sizes when a row cannot be served, so
`make check-trend-list-matrix` inside `make ci-unit` depended on the Hub's answer of the hour.

These tests pin the seam that fixes the root: `_hub_json` — the ONE Hub entry point behind `_tree`,
`gguf_repo`'s search and `mlx_repos`/`tensorfold_repos` — replays `tests/fixtures/hub-snapshot.json`
instead of fetching, so `matrix()` is a pure function of the vendored registry plus that recording.

The live comparison of `tests/test_trend_list_matrix.py` is NOT touched here (PR #1077's lane owns
that file); this module is the hermetic half.
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
from scripts import model_engine_pick as mp
from scripts import trend_list_matrix as tlm

FIXTURE = REPO / "tests" / "fixtures" / "trend-list-matrix.json"
SNAPSHOT = REPO / "tests" / "fixtures" / "hub-snapshot.json"


# -- helpers ------------------------------------------------------------------------------------
def _no_network(monkeypatch):
    """Every HTTP request a test makes raises, so a live read is a visible failure."""
    def refuse(*_a, **_k):
        raise AssertionError("the run reached the network: this path must be pure")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)


def _snapshot_doc() -> dict:
    return json.loads(SNAPSHOT.read_text())


def _first_tree_url(doc: dict) -> str:
    return next(url for url, entry in doc["trees"].items() if entry)


def _tmp_snapshot(tmp_path: Path, doc: dict) -> Path:
    path = tmp_path / "hub-snapshot.json"
    path.write_text(json.dumps(doc))
    return path


def _visible(answer) -> list:
    """What the consumers read from a Hub answer: file identity for a tree, repo id for a search."""
    if answer and "path" in answer[0]:
        return [(f["path"], f["size"], f["type"]) for f in answer]
    return [h["id"] for h in answer]


class _Hub(BaseHTTPRequestHandler):
    """A local stand-in for the Hub API: answers the recording's own URLs with its own answers."""

    doc: dict = {}

    def do_GET(self):  # noqa: N802 (http.server's spelling)
        url = f"https://huggingface.co{self.path}"  # the recording is keyed by Hub URL
        entry = self.doc["trees"].get(url)
        if entry is not None:
            body = [{"path": p, "size": s, "type": "file"} for p, s in entry]
        else:
            entry = self.doc["searches"].get(url)
            if entry is None:
                self.send_error(404)
                return
            body = [{"id": i} for i in entry]
        payload = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):  # noqa: A002 (BaseHTTPRequestHandler's own name)
        pass


@pytest.fixture()
def hub(monkeypatch):
    """A live HTTP server over the recording's answers, with `mp.HF` pointed at it."""
    doc = _snapshot_doc()
    handler = type("_HubAt", (_Hub,), {"doc": doc})
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(mp, "HF", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.delenv(mp.HUB_SNAPSHOT_ENV, raising=False)
    monkeypatch.setattr(mp, "_TREE_CACHE", {})
    try:
        yield doc
    finally:
        server.shutdown()
        server.server_close()


# -- the gate is hermetic -----------------------------------------------------------------------
def test_the_check_reproduces_the_fixture_with_no_route(monkeypatch):
    """`--check` rebuilds the committed matrix from the recording, with no route at all."""

    # Given the committed recording and every HTTP entry point refusing to run
    _no_network(monkeypatch)
    monkeypatch.delenv(mp.HUB_SNAPSHOT_ENV, raising=False)
    monkeypatch.setattr(sys, "argv", ["trend_list_matrix.py", "--check"])

    # When  the hermetic gate's command runs
    rc = tlm.main()

    # Then  it exits 0 — `--check` returns 0 only when the matrix it built equals the committed
    #       file's bytes, so this single run is the byte-identity proof, made with no route at all
    assert rc == 0


def test_the_replay_ignores_the_hub_disk_cache(monkeypatch, tmp_path):
    """A replay answers from the recording even when a stale Hub cache entry exists."""

    # Given a poisoned Hub disk-cache entry for a URL the matrix reads
    doc = _snapshot_doc()
    url = _first_tree_url(doc)
    repo = url.split("/api/models/", 1)[1].split("/tree/", 1)[0]
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    cache_dir = tmp_path / "cache" / "llgenie" / "hub"
    poison = cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".json")
    cache_dir.mkdir(parents=True)
    poison.write_text(json.dumps([{"path": "poison.gguf", "size": 1, "type": "file"}]))
    monkeypatch.setattr(mp, "_TREE_CACHE", {})

    # When  that URL is read through the committed recording
    with mp.hub_snapshot_file(SNAPSHOT):
        answer = mp._tree(repo)

    # Then  the recorded answer is used, not the cache, and replay wrote nothing of its own
    assert [f["path"] for f in answer] == [p for p, _ in doc["trees"][url]]
    assert [p.name for p in cache_dir.iterdir()] == [poison.name]


def test_a_url_missing_from_the_recording_is_loud(monkeypatch, tmp_path):
    """A gap in a recording raises, and never becomes a live read."""

    # Given a recording with one URL the matrix reads removed
    doc = _snapshot_doc()
    url = _first_tree_url(doc)
    repo = url.split("/api/models/", 1)[1].split("/tree/", 1)[0]
    doc["trees"].pop(url)
    path = _tmp_snapshot(tmp_path, doc)
    _no_network(monkeypatch)
    monkeypatch.delenv(mp.HUB_SNAPSHOT_ENV, raising=False)

    # When  that URL is read under the recording
    with pytest.raises(mp.HubSnapshotMissing) as excinfo, mp.hub_snapshot_file(path):
        mp._tree(repo)

    # Then  the failure names the URL (no HTTP was attempted: `_no_network` would have raised first)
    assert url in str(excinfo.value)


def test_the_mlx_and_tensorfold_searches_propagate_a_gap(monkeypatch, tmp_path):
    """The searches' broad `except Exception` cannot swallow a gap in a recording."""

    # Given a recording with the MLX and TensorFold search answers removed
    doc = _snapshot_doc()
    model = {"hf": "ornith-ai/Ornith-1.5-9B"}
    doc["searches"] = {u: v for u, v in doc["searches"].items()
                       if "filter=mlx" not in u and "author=TensorFold" not in u}
    path = _tmp_snapshot(tmp_path, doc)
    _no_network(monkeypatch)
    monkeypatch.delenv(mp.HUB_SNAPSHOT_ENV, raising=False)

    # When  each search runs under it
    with mp.hub_snapshot_file(path):
        for search in (mp.mlx_repos, mp.tensorfold_repos):
            # Then  the gap is raised instead of reported as "publishes none"
            with pytest.raises(mp.HubSnapshotMissing):
                search(model)


# -- default behaviour is unchanged -------------------------------------------------------------
def test_the_default_path_is_still_the_live_read(hub, monkeypatch, tmp_path):
    """With no recording set, `_hub_json` is the live Hub read it always was."""

    # Given a live Hub (a local server standing in for it) and no recording
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(mp, "HUB_CACHE_TTL", 0)
    url = _first_tree_url(hub)
    repo = url.split("/api/models/", 1)[1].split("/tree/", 1)[0]

    # When  `_tree` is asked for that repo with nothing replayed
    answer = mp._tree(repo)

    # Then  the real transport answered, so the live path is untouched by the seam
    assert [f["path"] for f in answer] == [p for p, _ in hub["trees"][url]]


def test_a_recording_round_trips_and_replay_is_exclusive(hub, monkeypatch, tmp_path):
    """A render's recording replays to the same answers, and one Hub source is enforced."""

    # Given a live read of one tree and one search, recorded
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(mp, "HUB_CACHE_TTL", 0)
    tree_url = _first_tree_url(hub)
    search_url = next(u for u in hub["searches"] if "filter=mlx" in u)
    with mp.hub_recording() as recorded:
        live_tree = mp._hub_json(tree_url)
        live_search = mp._hub_json(search_url)

    # When  that recording is written and replayed
    path = mp.write_hub_snapshot(tmp_path / "snap.json", recorded)
    with mp.hub_snapshot_file(path):
        replayed_tree = mp._hub_json(tree_url)
        replayed_search = mp._hub_json(search_url)

        # Then  what the consumers read is the same from both, and recording inside a replay is refused
        assert _visible(replayed_tree) == _visible(live_tree)
        assert _visible(replayed_search) == _visible(live_search)
        with pytest.raises(ValueError):
            with mp.hub_recording():
                pass
