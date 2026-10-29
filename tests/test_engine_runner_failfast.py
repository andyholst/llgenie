#!/usr/bin/env python3
"""A server that dies before it is ready must say WHY (engine runner).

Found on this host: `llgenie-engine-llama-cpp` on a ternary PQ2 GGUF
(`prism-ml/Ternary-Bonsai-2-27B-gqgf`, tensor type 142) printed the launch line and then
exited 1 in two seconds with no reason. llama-server HAD printed the reason
(`tensor 'output.weight' has invalid ggml type 142`) into
`$TMPDIR/engine-runner-serve.log` — a file inside a container the launcher removes on exit,
so the one line a user needs was thrown away and the engine looked merely "stuck", not
"cannot read this model".

These tests drive the REAL `serve_plan` with a launch command that dies, which is the shape
no happy-path test covers.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import scripts.engine_runner as er  # noqa: E402  (the real runner, never a copy)


def _dying_plan(message: str = "invalid ggml type 142", rc: int = 3) -> dict:
    """A plan whose server prints one error line and exits, never opening its port."""
    return {
        "id": "demo", "backend": "cuda",
        "health": "/v1/models",
        "launch": f"echo '{message}' >&2; exit {rc}",
    }


def test_a_server_that_dies_before_ready_prints_its_own_error(tmp_path, monkeypatch, capsys):
    """The engine's reason must survive the container, not just the exit code."""

    # Given a launch that fails on load, with its output going to the per-run log
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    # When  the runner serves it
    code = er.serve_plan(_dying_plan(), "model.gguf", "127.0.0.1", 1, ready_timeout=10)

    # Then  the exit code is the server's, and the reason is on stderr
    err = capsys.readouterr().err
    assert code == 3, f"the server's own exit code must not be replaced: {code}"
    assert "FAIL demo/cuda" in err, err
    assert "invalid ggml type 142" in err, f"the engine's own error was swallowed: {err!r}"


def test_the_reported_exit_code_is_the_servers(tmp_path, monkeypatch, capsys):
    """A different failure mode reports that code, not a generic 1."""

    # Given a launch that exits 7
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    # When  it runs
    code = er.serve_plan(_dying_plan("boom", rc=7), "m", "127.0.0.1", 1, ready_timeout=10)

    # Then  the caller sees 7 and the word FAIL
    assert code == 7
    assert "FAIL demo/cuda" in capsys.readouterr().err
