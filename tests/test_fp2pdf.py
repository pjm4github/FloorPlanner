"""`fp2pdf`'s four hygiene fixes (0072-ruling.md sec2), the same class
`fp2dxf.py` was already fixed for five days earlier (0038-ruling.md):

  1. a THIRD wall-thickness table, disagreeing with the normative
     `floorplanner.design.validate.STD_T` in 4 of 7 rows -- now read live
     via `fp2dxf.py`'s own by-path loader, reused not transcribed.
  2. `raise SystemExit` inside `convert()` -- a Qt menu handler's
     `try/except Exception` around this call would never see it coming.
  3. `print()` inside `convert()`, and no result object -- now returns a
     `ConvertResult` (sheets written + warnings) and prints nothing.
  4. `reportlab` imported at module top, in no requirements file -- an
     unguarded import would stop the whole app starting for anyone
     without it (D40). Now deferred into `convert()`, raising `ValueError`
     with a reason if missing, so the MODULE itself always imports.

Qt-free by construction, like `fp2dxf.py` -- `fp2pdf` imports nothing from
`floorplanner` (`floorplanner/export/__init__.py`'s own docstring), so this
needs no `fp`/`win` fixture.
"""
import json
import re
from pathlib import Path

import pytest

from floorplanner.export import fp2pdf
from floorplanner.export.fp2pdf import ConvertResult, convert

pytestmark = pytest.mark.io

_MINIMAL_LEVEL = {"id": "L1", "name": "Main", "elevation_in": 0.0,
                  "height_in": 96.0, "kind": "storey", "reference": False}
_MINIMAL_META = {"title": "Test House", "subtitle": "", "author": "Tester",
                 "assembly_note": "note", "dim_note": "dim"}


def _rect_doc():
    """A v5 doc with one closed rectangle -- enough for `Sheet._frame()`,
    which needs at least one wall (empty-level PDF generation is a
    separate, pre-existing limitation, not part of this receipt)."""
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [_MINIMAL_LEVEL],
        "vertices": [
            {"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 240, "y": 0},
            {"id": "v3", "x": 240, "y": 200}, {"id": "v4", "x": 0, "y": 200},
        ],
        "walls": [
            {"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
             "type": "exterior", "openings": []},
            {"id": "w2", "level": "L1", "v1": "v2", "v2": "v3",
             "type": "exterior", "openings": []},
            {"id": "w3", "level": "L1", "v1": "v3", "v2": "v4",
             "type": "exterior", "openings": []},
            {"id": "w4", "level": "L1", "v1": "v4", "v2": "v1",
             "type": "exterior", "openings": []},
        ],
        "rooms": [], "furnishings": [],
    }


# ---------------------------------------------------------------------------
# (1) the thickness table
# ---------------------------------------------------------------------------

def test_thickness_table_matches_std_t_not_a_transcribed_copy():
    """Not a test of the seven current numbers (0072 sec6's own instruction)
    -- compares against the real, independently-imported STD_T, so a future
    change to either table is caught by disagreement, not by both moving
    together."""
    from floorplanner.design.validate import STD_T
    assert fp2pdf._default_thickness() == STD_T


# ---------------------------------------------------------------------------
# (2) SystemExit -> ValueError
# ---------------------------------------------------------------------------

def test_convert_raises_valueerror_not_systemexit_on_a_non_v5_doc(tmp_path):
    """pytest.raises(ValueError) does NOT catch SystemExit (it is not an
    Exception subclass) -- if the old bug were present this test would
    ERROR, not pass, which is the differential this receipt needs."""
    with pytest.raises(ValueError, match="v5"):
        convert({"format": "x"}, tmp_path / "out.pdf", _MINIMAL_META)


# ---------------------------------------------------------------------------
# (3) a result object, nothing printed
# ---------------------------------------------------------------------------

def test_convert_returns_a_result_and_prints_nothing(tmp_path, capsys):
    pytest.importorskip("reportlab")
    out = tmp_path / "out.pdf"
    result = convert(_rect_doc(), out, _MINIMAL_META)
    assert isinstance(result, ConvertResult)
    assert result.out == out
    assert result.sheets == ["sheet P1: Main"]
    assert result.warnings == []
    assert out.exists()
    captured = capsys.readouterr()
    assert captured.out == "", f"convert() printed: {captured.out!r}"


# ---------------------------------------------------------------------------
# (4) reportlab is optional -- the MODULE always imports, only an actual
# export attempt fails, with a reason
# ---------------------------------------------------------------------------

def test_module_imports_without_reportlab():
    """The regression this receipt exists for: `from reportlab... import`
    at module top would make the whole module (and anything that imports
    it, including the app's own menu wiring once built) fail to import at
    all without reportlab installed. Importing fp2pdf here, in a suite that
    does not require reportlab, already partly proves this; PAGE is
    computed with no reportlab symbol at module scope, checked directly."""
    src = Path(fp2pdf.__file__).read_text(encoding="utf-8")
    top = src.split("\ndef ", 1)[0]           # everything before the first def
    assert "import reportlab" not in top and "from reportlab" not in top, (
        "reportlab is imported at module top -- the module (and its "
        "importer) can no longer load without it installed")


def test_module_imports_with_fp2dxf_absent():
    """0077-ruling.md sec5's own receipt: fp2pdf used to exec the whole of
    fp2dxf.py by path just to borrow its thickness loader, so the PDF
    exporter depended on the DXF one -- backwards for a package whose own
    docstring is about running "without dragging in" anything. Renames
    fp2dxf.py aside (restored in `finally`, whatever happens) and loads a
    SEPARATE copy of fp2pdf.py, under a throwaway module name so the real
    `floorplanner.export.fp2pdf` already in `sys.modules` is untouched --
    fp2dxf.py genuinely absent from disk, not merely unimported, and
    _stdt.py's own relative path to `design/validate.py` still resolves
    because fp2pdf.py stays in its real location throughout."""
    import importlib.util
    import sys
    real_dir = Path(fp2pdf.__file__).resolve().parent
    fp2dxf_path = real_dir / "fp2dxf.py"
    hidden = real_dir / "fp2dxf.py.hidden-for-test"
    fp2dxf_path.rename(hidden)
    try:
        spec = importlib.util.spec_from_file_location(
            "_iso_fp2pdf_no_fp2dxf", real_dir / "fp2pdf.py")
        mod = importlib.util.module_from_spec(spec)
        # fp2pdf.py's own ConvertResult is a @dataclass, which resolves
        # type hints via sys.modules[cls.__module__] -- register under
        # this throwaway name before exec_module, same as fp2pdf.py's own
        # loader does for fp2dxf.py's ConvertResult.
        sys.modules[spec.name] = mod
        try:
            spec.loader.exec_module(mod)  # must not raise looking for fp2dxf.py
        finally:
            del sys.modules[spec.name]
    finally:
        hidden.rename(fp2dxf_path)
    from floorplanner.design.validate import STD_T
    assert mod._default_thickness() == STD_T


def test_convert_degrades_to_a_valueerror_when_reportlab_is_missing(
        monkeypatch, tmp_path):
    """Forces the missing-dependency path regardless of whether reportlab
    happens to be installed in this environment -- 0072 sec6's own
    instruction: "test it with the import actually blocked, not by reading
    the code." """
    import builtins
    real_import = builtins.__import__

    def blocked(name, *a, **kw):
        if name == "reportlab" or name.startswith("reportlab."):
            raise ImportError("simulated: reportlab not installed")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ValueError, match="reportlab"):
        convert(_rect_doc(), tmp_path / "out.pdf", _MINIMAL_META)


# ---------------------------------------------------------------------------
# the fourth, smaller hygiene item: an explicit encoding on the CLI's read
# ---------------------------------------------------------------------------

def test_main_reads_the_design_file_with_an_explicit_encoding():
    """A source check, not a behavioural one: the platform-default-encoding
    failure this guards against (cp1252 misreading a UTF-8-saved design,
    0043-report.md's own fourth hygiene item for fp2dxf.py) is platform-
    dependent, so a specific poison byte sequence would not reliably
    reproduce it on every CI leg this suite runs on. What is checked is
    that the call site names its encoding at all."""
    src = Path(fp2pdf.__file__).read_text(encoding="utf-8")
    m = re.search(r"a\.design\.read_text\(([^)]*)\)", src)
    assert m is not None, "main() no longer reads a.design.read_text(...)"
    assert "encoding" in m.group(1), (
        "a.design.read_text() has no explicit encoding -- reads the "
        "platform default instead of the UTF-8 every design is written as")


def test_main_round_trips_a_design_via_the_cli(tmp_path):
    pytest.importorskip("reportlab")
    design_path = tmp_path / "design.json"
    design_path.write_text(json.dumps(_rect_doc()), encoding="utf-8")
    out_path = tmp_path / "out.pdf"
    fp2pdf.main([str(design_path), "-o", str(out_path),
                "--title", "Test House", "--author", "Tester"])
    assert out_path.exists()


# ---------------------------------------------------------------------------
# 0118-ruling.md sec2 -- D82: drifted stations pile up, so cluster first,
# then round the SURVIVING stations before differencing (telescoping labels)
# ---------------------------------------------------------------------------

def test_cluster_stations_merges_a_drifted_pair_within_one_inch():
    """The sheet's own resolution is 1" after D82's whole-inch labels -- a
    drifted wall's near-duplicate station 0.07" from a clean one used to
    mint its own extension line, tick and rotated label crammed onto a
    fraction of a point (the pile-up Patrick reported)."""
    merged = fp2pdf.cluster_stations([100.0, 100.07, 250.0])
    assert len(merged) == 2
    assert merged[0] == pytest.approx((100.0 + 100.07) / 2)
    assert merged[1] == 250.0


def test_cluster_stations_keeps_a_two_inch_outlier_separate():
    """0118-ruling.md sec2's own boundary: 1.6"-3" drift outliers SURVIVE
    clustering and show as honest slivers -- exactly the walls worth
    snapping, not hidden by this presentation-side fix."""
    merged = fp2pdf.cluster_stations([100.0, 102.0])
    assert merged == [100.0, 102.0]


def test_cluster_stations_chains_a_transitive_run():
    """A run of stations each within tol of its predecessor collapses to
    one cluster even though the run's own span (0.9) exceeds a single
    pairwise gap -- documented behaviour, not an accident."""
    merged = fp2pdf.cluster_stations([0.0, 0.5, 0.9])
    assert len(merged) == 1


def test_rounded_station_labels_telescope_where_naive_rounding_would_not():
    """The classic drafting bug: rounding each segment's own length
    independently does not sum to the rounded overall. Stations 0.0, 10.4,
    20.6, 31.0 -- naive per-segment rounding gives 10 + 10 + 10 = 30, one
    inch short of round(31.0) = 31. Rounding the STATIONS first and
    differencing (0118-ruling.md sec2 step 2, `_rounded_stations`) is what
    `dim_row_x`/`dim_row_y` now do, and it telescopes by construction."""
    coords = [0.0, 10.4, 20.6, 31.0]
    naive = [round(b - a) for a, b in zip(coords, coords[1:], strict=False)]
    assert sum(naive) != round(coords[-1] - coords[0]), (
        "the naive approach was supposed to disagree -- fixture no longer "
        "demonstrates the bug this receipt exists for")
    rounded = fp2pdf._rounded_stations(coords)
    segments = [b - a for a, b in zip(rounded, rounded[1:], strict=False)]
    assert sum(segments) == rounded[-1] - rounded[0]
    assert rounded[-1] - rounded[0] == round(coords[-1] - coords[0])


def _drift_pair_doc():
    """Two independent walls whose facing ends sit 0.07" apart on the same
    line -- exactly the drift D61/D63/D64/D65 leave behind, and the shape
    of Patrick's own complaint: "when walls are slightly off then there is
    a mess of dimensions on top of each other"."""
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [_MINIMAL_LEVEL],
        "vertices": [
            {"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 100.0, "y": 0},
            {"id": "v3", "x": 100.07, "y": 0}, {"id": "v4", "x": 200.0, "y": 0},
        ],
        "walls": [
            {"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
             "type": "exterior", "openings": []},
            {"id": "w2", "level": "L1", "v1": "v3", "v2": "v4",
             "type": "exterior", "openings": []},
        ],
        "rooms": [], "furnishings": [],
    }


def test_features_collapses_a_0_07_inch_drift_pair_into_one_station():
    """Fail-first per 0118-ruling.md sec4's own receipt list: before
    clustering, `_features()` minted one station per distinct (rounded to
    0.001") x value -- four raw endpoints here (0, 100.0, 100.07, 200.0)
    become FOUR stations, not three, and the 0.07" pair renders as its own
    crammed dimension segment."""
    sheet = fp2pdf.Sheet(None, _drift_pair_doc(), _MINIMAL_LEVEL,
                          fp2pdf._default_thickness(), False, _MINIMAL_META)
    fx, _fy = sheet._features()
    assert len(fx) == 3, f"expected the drifted pair to merge, got {fx}"
    assert fx[0] == 0.0
    assert fx[-1] == 200.0


# ---------------------------------------------------------------------------
# 0118-ruling.md sec3 -- D81: one symbol per catalog door_type, keyed off
# the real vocabulary (`walls.py:_paint_door`'s), not the never-true
# `door_type == "sliding"` check
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("door_type,expected", [
    ("LH", "swing"), ("RH", "swing"), ("", "swing"),
    ("FRENCH", "french"), ("BIFOLD", "bifold"), ("POCKET", "pocket"),
    ("SLIDER", "slider"), ("DOORWAY", "doorway"),
    ("GARAGE-1", "garage"), ("GARAGE-2", "garage"),
    ("garage-1", "garage"),          # case-insensitive, like the rest
])
def test_door_symbol_dispatches_every_catalog_value(door_type, expected):
    """`floorplanner/config.py:DOOR_TYPES`'s full vocabulary, one assertion
    per value -- 0118-ruling.md sec4's own receipt list."""
    assert fp2pdf._door_symbol("door", door_type) == expected


def test_door_symbol_flags_sliding_as_unknown_not_a_silent_swing():
    """D81's actual finding: `door_type == "sliding"` can never be true
    against this catalog, so it silently fell through to a generic swing.
    It must now be named, not absorbed."""
    assert fp2pdf._door_symbol("door", "sliding") == "unknown"
    assert fp2pdf._door_symbol("door", "made-up-type") == "unknown"


def test_door_symbol_gate_is_always_a_swing_regardless_of_door_type():
    """`door_type` is schema-documented as meaningful only when kind ==
    "door" -- a gate's own field (if present at all) must not steer it."""
    assert fp2pdf._door_symbol("gate", "anything") == "swing"


def test_door_symbol_non_door_kind_is_not_a_door_at_all():
    assert fp2pdf._door_symbol("window", "LH") is None


def _door_doc(door_type):
    """One 200" wall carrying a single door/gate opening of `door_type`,
    centred, wide enough for FRENCH's half-width leaves to stay positive."""
    kind = "gate" if door_type == "GATE" else "door"
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [_MINIMAL_LEVEL],
        "vertices": [
            {"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 200.0, "y": 0},
            {"id": "v3", "x": 200.0, "y": 150.0},
            {"id": "v4", "x": 0, "y": 150.0},
        ],
        "walls": [
            {"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
             "type": "exterior", "openings": [
                 {"id": "o1", "kind": kind, "code": "3068",
                  "anchor": {"from": "center", "offset_in": 0.0},
                  "door_type": door_type, "hinge": "v1",
                  "swings_toward": "left"}]},
            {"id": "w2", "level": "L1", "v1": "v2", "v2": "v3",
             "type": "exterior", "openings": []},
            {"id": "w3", "level": "L1", "v1": "v3", "v2": "v4",
             "type": "exterior", "openings": []},
            {"id": "w4", "level": "L1", "v1": "v4", "v2": "v1",
             "type": "exterior", "openings": []},
        ],
        "rooms": [], "furnishings": [],
    }


@pytest.mark.parametrize("door_type", [
    "LH", "RH", "FRENCH", "BIFOLD", "POCKET", "SLIDER", "DOORWAY",
    "GARAGE-1", "GARAGE-2", "GATE",
])
def test_convert_renders_every_catalog_door_type_without_raising(
        tmp_path, door_type):
    pytest.importorskip("reportlab")
    out = tmp_path / "out.pdf"
    result = convert(_door_doc(door_type), out, _MINIMAL_META)
    assert out.exists()
    assert result.warnings == []


@pytest.mark.parametrize("door_type", ["sliding", "made-up-type"])
def test_convert_warns_on_an_unrecognized_door_type_but_still_renders(
        tmp_path, door_type):
    """D81 sec3's own instruction: an unknown value draws the generic
    swing AND is listed in `ConvertResult.warnings` -- not silently
    absorbed, which is exactly how `"sliding"` went unnoticed the first
    time."""
    pytest.importorskip("reportlab")
    out = tmp_path / "out.pdf"
    result = convert(_door_doc(door_type), out, _MINIMAL_META)
    assert out.exists()
    assert len(result.warnings) == 1
    assert door_type in result.warnings[0]
