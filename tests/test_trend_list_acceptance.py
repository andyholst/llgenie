"""Acceptance criteria of the llgenie trend list on Linux AND Mac hardware (issue #114,
OpenSpec fix-mac-trend-pick-tensorfold). One matrix, every backend llgenie supports:

  linux: cuda, rocm, vulkan, cpu        mac: metal (Apple-Silicon unified memory)

For every (backend, card size) the list must satisfy the same invariants, whatever
the README says this week:

  AC1  rows   = exactly the README "Most loved" models whose VRAM tier fits the card,
               in README order (nothing added, nothing dropped, nothing reordered);
  AC2  number = only servable rows are numbered, 1..N without gaps, and `--select N`
               / the prompt / `--auto` take exactly row N (1 for --auto);
  AC3  engine = every offered engine runs on this host: the host's own variant
               (metal = native) or a cpu image, never a disabled #103 image, never a
               variant of another backend (no metal on linux, no cuda on a mac);
  AC4  order  = engines ranked: a figure proven on this host's card class first
               (issue #225), then a same-backend figure from a bigger/unknown card,
               then other hardware, then a datacenter figure, then supported-only,
               then by t/s within a rank;
  AC5  fit    = every engine has a local copy or a download plan that fits the
               host's weight budget (TensorFold: its own checkpoint, Strata: its
               setup.py files);
  AC6  why    = a row that cannot be served states a non-empty reason and has no engine;
  AC7  label  = the t/s label is `model_engine_pick.tps_label` (issue #225): bare
               t/s only for a figure proven on this host's card class;
  AC8  header = the printed header names the detected backend and card size.

The list is checked without the prompt (`llgenie --trend` prints the same rows the
prompt asks from). Real vendored registry + live Hugging Face API, no Hub mocks."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import hf_auth  # noqa: E402
sys.path.insert(0, str(REPO / "tests"))
import engine_image as ei  # noqa: E402
import model_engine_pick as mp  # noqa: E402
import sync_registry as sr  # noqa: E402

SERVE = REPO / "scripts" / "llgenie_serve.py"
README = REPO / "data" / "trending-README.md"
HUB_CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
RAM = 64  # system RAM of the Linux hosts (GiB); a Mac's RAM is its card

# (platform, backend, card GiB): every backend, small and large cards
HOSTS = [
    ("linux", "cuda", 8), ("linux", "cuda", 16), ("linux", "cuda", 24),
    ("linux", "rocm", 16), ("linux", "rocm", 24),
    ("linux", "vulkan", 16), ("linux", "vulkan", 48),
    ("linux", "cpu", 16), ("linux", "cpu", 48),
    ("mac", "metal", 16), ("mac", "metal", 48), ("mac", "metal", 128),
]
IDS = [f"{p}-{b}-{g}gb" for p, b, g in HOSTS]
ROW = re.compile(r"^\s+(--|\d+\.)\s{2}(.+?)\s+(trending|recent|stale)\s+trend")


def _ram(backend: str, gb: int) -> int:
    return gb if backend == "metal" else RAM


def _env(tmp_path: Path, backend: str, gb: int) -> dict:
    env = {**os.environ, "LLAMA_MODELS_ROOT": str(tmp_path), "LLAMA_BACKEND": backend,
           "LLAMA_RAM_BYTES": str(gb * 2**30), "LLGENIE_SYSTEM_RAM_BYTES": str(_ram(backend, gb) * 2**30),
           "HOME": str(tmp_path / "home"), "XDG_CACHE_HOME": str(HUB_CACHE)}
    env.pop("LLGENIE_REGISTRY_SRC", None)
    return env


def _readme_rows() -> list[tuple[str, int]]:
    """(name, VRAM GB) parsed straight from the vendored README markdown (the list a
    user reads on GitHub), independent of data/models.json.

    The VRAM column is looked up BY NAME in the table header — upstream reorders and
    restyles columns (`16GB`, `**12GB**<br><sub>stated by the source …</sub>`, `8`, `CPU`),
    and any of those must read the same as production's `mp._num` (16, 12, 8, 0)."""
    section = README.read_text().split(sr.MOST_LOVED, 1)[1].split("\n## ", 1)[0]
    lines = section.splitlines()
    header = next(l for l in lines if l.startswith("| Model"))
    vram_at = [c.strip() for c in header.strip().strip("|").split("|")].index("VRAM")
    rows = []
    for line in lines:
        m = re.match(r"^\| \[\*\*(.+?)\*\*\]", line)
        if m:
            cells = [c.strip() for c in line.split(" | ")]
            # "**12GB**<br><sub>stated by the source · …</sub>" -> "12GB"
            vram = cells[vram_at].split("<br>", 1)[0].replace("*", "").strip()
            rows.append((m.group(1), int(mp._num(vram))))
    return rows


_CACHE: dict = {}


def _offer(tmp_path: Path, backend: str, gb: int) -> list[dict]:
    key = (backend, gb)
    if key not in _CACHE:
        os.environ.pop("LLGENIE_REGISTRY_SRC", None)
        _CACHE[key] = mp.offer(mp.load_registry(), backend, gb, root=tmp_path, ram_gb=_ram(backend, gb))
    return _CACHE[key]


def _cli(tmp_path: Path, backend: str, gb: int, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SERVE), *args], env=_env(tmp_path, backend, gb),
                          stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          timeout=hf_auth.TOP_TIER_DRY_RUN_TIMEOUT)


def test_readme_parser_reads_the_vendored_list():
    # Given the vendored README

    # When its "Most loved" table is parsed
    rows = _readme_rows()

    # Then it is the registry's model list in the same order, and each row's README VRAM is
    # the store's measured minimum (the tier is a display bucket that rounds differently —
    # issue #669) within the 1 GB the column rounds away
    reg = mp.load_registry()["models"]
    assert [n for n, _ in rows] == [m["name"] for m in reg]
    for (name, vram), model in zip(rows, reg):
        stated = mp.vram_min_gb(model) or mp._num(model.get("vram_tier"))
        assert abs(stated - vram) <= 1, f"{name}: README {vram}GB vs the store's {stated}GB"


@pytest.mark.parametrize("platform,backend,gb", HOSTS, ids=IDS)
def test_ac1_rows_are_the_readme_models_that_fit_in_readme_order(tmp_path, platform, backend, gb):
    # Given the README list and a host
    ram = _ram(backend, gb)

    # When llgenie builds its list
    rows = _offer(tmp_path, backend, gb)

    # Then it is exactly the registry's models this host fits, in README order — the
    # fit is the product's own decision (VRAM floor AND the stated system-RAM floor,
    # issue #669/#414), while the ORDER comes from the README the store was synced with.
    expected = [m["name"] for m in mp.load_registry()["models"] if mp.fits(m, gb, ram)]
    assert [r["model"]["name"] for r in rows] == expected


def test_the_vram_gate_reads_the_field_the_readme_agrees_with():
    """The gate reads the store's measured minimum (`vram_min`), not the display bucket.

    Measured on the 2026-10-27 store: the README's VRAM column differs from `vram_min` on
    **0 of 112** rows (allowing the 1 GB the column rounds away) and from `vram_tier` on
    **36 of 112**. So `vram_min` IS the column, and the label is a different number
    (issue #669).
    """
    # Given every registry row and the README's VRAM column for it
    reg = {m["name"]: m for m in mp.load_registry()["models"]}

    def off_by(field) -> list[str]:
        bad = []
        for name, vram in _readme_rows():
            model = reg.get(name)
            if model is None:
                continue
            value = mp.vram_min_gb(model) if field == "vram_min" else mp._num(model.get("vram_tier"))
            if value is not None and abs(value - vram) > 1:   # 1 GB is the column's rounding
                bad.append(name)
        return bad

    # When  each field is compared with the column
    min_bad, tier_bad = off_by("vram_min"), off_by("vram_tier")

    # Then  the gate's field matches the column and the tier does not
    assert min_bad == [], f"vram_min disagrees with the README column on {len(min_bad)} rows"
    assert len(tier_bad) > 0, "the tier and the column agree here; this test would prove nothing"


@pytest.mark.parametrize("platform,backend,gb", HOSTS, ids=IDS)
def test_ac3_every_engine_runs_on_this_host(tmp_path, platform, backend, gb):
    # Given the list for a host
    rows = _offer(tmp_path, backend, gb)

    # When the engines of every servable row are checked
    engines = [e for r in rows for e in r["engines"]]

    # Then each is this host's variant or a cpu image, never disabled, never another backend's
    for e in engines:
        assert e["variant"] in (backend, "cpu"), e
        assert not ei.disabled(e["id"], e["variant"]), e
        if platform == "linux":
            assert e["variant"] != "metal", e
        else:
            assert e["variant"] in ("metal", "cpu"), e

    # And a Metal-native engine is only ever offered natively on a mac
    native = {e["id"] for e in engines if e["variant"] == "metal"}
    assert native <= mp.metal_engines()


@pytest.mark.parametrize("platform,backend,gb", HOSTS, ids=IDS)
def test_ac4_engines_are_ranked_same_hardware_then_other_then_supported(tmp_path, platform, backend, gb):
    # Given the list for a host
    rows = _offer(tmp_path, backend, gb)

    # When each row's engine order is read
    for r in rows:
        keys = [(e["rank"], -e["tps"]) for e in r["engines"]]

        # Then it is sorted by rank, then t/s descending; rank 0 == measured on this hardware
        assert keys == sorted(keys), r["model"]["name"]
        for e in r["engines"]:
            # A rank 0 row is one proven on this host: its backend matches AND (on a card
            # host) the figure ran on a card of this host's class or smaller (issue #225)
            assert e["same_hw"] == (e["measured_on"] == mp.HOST_TO_MEASURED[backend]
                                    and e["card_class"] == "proven")


@pytest.mark.parametrize("platform,backend,gb", HOSTS, ids=IDS)
def test_ac5_every_engine_has_a_fitting_download_or_local_copy(tmp_path, platform, backend, gb):
    # Given the list for a host and its weight budget
    rows = _offer(tmp_path, backend, gb)

    # When each offered engine's model source is resolved
    for r in rows:
        budget = mp.weight_budget_gb(gb, mp.is_moe(r["model"]), _ram(backend, gb), backend) * 2**30
        for e in r["engines"]:
            plan, local = mp.engine_plan(r, e), mp.engine_local(r, e)

            # Then there is a plan (or a local copy) in a format the engine reads
            assert plan or local, (r["model"]["name"], e["id"])
            assert e["use_format"] in e["formats"]

            # And the plan fits the budget (Strata sizes itself from its setup.py)
            if plan and e["id"] != "strata":
                assert plan["size"] <= budget, (r["model"]["name"], e["id"], plan["repo"])

            # And TensorFold only ever downloads TensorFold's own checkpoints
            if plan and e["id"] == "tensorfold":
                assert plan["repo"].startswith("TensorFold/") and "-MLX-" in plan["repo"]


@pytest.mark.parametrize("platform,backend,gb", HOSTS, ids=IDS)
def test_ac6_unservable_rows_say_why_and_offer_nothing(tmp_path, platform, backend, gb):
    # Given the list for a host
    rows = _offer(tmp_path, backend, gb)

    # When the rows are split into servable and not
    for r in rows:
        # Then a row is servable exactly when it has an engine, otherwise it says why
        assert bool(r["engines"]) != bool(r["why"]), (r["model"]["name"], r["why"])


@pytest.mark.parametrize("platform,backend,gb", HOSTS, ids=IDS)
def test_ac2_ac7_ac8_printed_list_numbering_labels_and_header(tmp_path, platform, backend, gb):
    # Given the rows llgenie computed for a host
    rows = _offer(tmp_path, backend, gb)

    # When `llgenie --trend` prints the list (no prompt)
    r = _cli(tmp_path, backend, gb, "--trend")

    # Then the header names the backend and the card (AC8)
    assert r.returncode == 0, r.stderr
    assert f"this card ({gb} GB, {backend})" in r.stdout

    # And one printed line per row, numbered 1..N only where servable (AC2)
    lines = [ln for ln in r.stdout.splitlines() if ROW.match(ln)]
    assert len(lines) == len(rows)
    n = 0
    for ln, row in zip(lines, rows):
        mark, name = ROW.match(ln).group(1), ROW.match(ln).group(2)
        assert name == row["model"]["name"]
        if row["why"]:
            assert mark == "--" and f"not here: {row['why']}" in ln
            continue
        n += 1
        assert mark == f"{n}."

        # And the t/s label is the ONE label rule: bare t/s only for a figure proven
        # on this host's card class, otherwise the card / backend it came from (AC7, #225)
        e = row["engines"][0]
        assert e["engine"] in ln
        assert mp.tps_label(e) in ln


@pytest.mark.parametrize("platform,backend,gb", [h for h in HOSTS if h[2] in (16, 48)],
                         ids=[i for i, h in zip(IDS, HOSTS) if h[2] in (16, 48)])
def test_ac2_select_n_and_auto_take_the_numbered_row(tmp_path, platform, backend, gb):
    # Given the servable rows of a host
    pick = [r for r in _offer(tmp_path, backend, gb) if not r["why"]]
    assert pick, "every host must have something to serve"

    # When `--select 1`, `--select N` (last) and `--auto` run dry
    runs = {1: _cli(tmp_path, backend, gb, "--select", "1", "--dry"),
            len(pick): _cli(tmp_path, backend, gb, "--select", str(len(pick)), "--dry")}
    auto = _cli(tmp_path, backend, gb, "--auto", "--dry")

    # Then each takes exactly that row and its top engine; --auto takes row 1
    for n, r in runs.items():
        assert r.returncode == 0, r.stderr
        row = pick[n - 1]
        assert f"Model  : {row['model']['name']}" in r.stdout
        assert f"Engine : {row['engines'][0]['engine']} [{row['engines'][0]['variant']}]" in r.stdout
    assert auto.returncode == 0, auto.stderr
    assert f"Model  : {pick[0]['model']['name']}" in auto.stdout

    # And --select past the end is refused with the valid range
    bad = _cli(tmp_path, backend, gb, "--select", str(len(pick) + 1), "--dry")
    assert bad.returncode != 0 and f"pick 1-{len(pick)}" in bad.stderr


def test_same_readme_different_hardware_gives_each_host_its_own_top_engine(tmp_path):
    """For each host, a row that HAS a figure measured on that host's hardware ranks it first.

    No model and no engine is pinned (issue #693) — the rows come from the store, so the
    invariant is AC4's first rank: when a row carries a figure measured on this host's
    class, that engine is the one offered first; a Metal figure is never the top engine on
    a cuda or cpu host when a CUDA/CPU one exists.
    """

    # Given the servable list of each host
    def rows(backend, gb):
        return [r for r in _offer(tmp_path, backend, gb) if not r["why"]]

    # When each host's list is walked
    checked = 0
    for backend, gb, want in (("metal", 48, "Metal"), ("cuda", 24, "CUDA"), ("cpu", 48, "CPU")):
        for row in rows(backend, gb):
            measured = {e["measured_on"] for e in row["engines"]}
            if want not in measured:
                continue        # nothing of this host's class for this row: the global order decides
            checked += 1

            # Then the engine offered first is the one measured on this host's hardware
            assert row["engines"][0]["measured_on"] == want, \
                f"{backend}/{gb}: {row['model']['name']} has a {want} figure but ranks " \
                f"{row['engines'][0]['measured_on']} first"

    # And the invariant was actually exercised on this store
    assert checked > 0, "no row carries a figure measured on its own host's class"
