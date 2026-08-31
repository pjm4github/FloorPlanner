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


# ---------------------------------------------------------------------------
# 0119-ruling.md sec3 / 0123-ruling.md sec3 item 1 -- dim_row_along shared by
# the two orthogonal rows (GREEN: no visible change, existing tests unchanged)
# ---------------------------------------------------------------------------

def test_convert_renders_the_rect_doc_unchanged_after_the_refactor(tmp_path):
    """The GREEN receipt: existing dimension tests unchanged, and the
    corpus telescoping census (docs/evidence/pdf_dimension_telescoping_census.py)
    re-run identical (964 raw -> 856 clustered, per 0121-report.md) --
    checked by hand alongside this receipt, not re-asserted here since it
    needs the real corpus, not a synthetic doc."""
    pytest.importorskip("reportlab")
    out = tmp_path / "out.pdf"
    result = convert(_rect_doc(), out, _MINIMAL_META)
    assert isinstance(result, ConvertResult)
    assert result.warnings == []
    assert out.exists()


# ---------------------------------------------------------------------------
# 0127-ruling.md / 0128-ruling.md -- opening stations leave EVERY row
# (bottom X, left Y, and the angled lanes); openings still DRAW
# ---------------------------------------------------------------------------

def _door_wall_doc():
    """One wall with a centred door vs. the same wall without one --
    isolates whether `_features()` reads the opening at all."""
    def doc(has_door):
        openings = [{"id": "o1", "kind": "door", "code": "3068",
                     "anchor": {"from": "center", "offset_in": 0.0},
                     "door_type": "LH", "hinge": "v1",
                     "swings_toward": "left"}] if has_door else []
        return {
            "format": "floorplanner-design", "version": 5,
            "levels": [_MINIMAL_LEVEL],
            "vertices": [{"id": "v1", "x": 0, "y": 0},
                         {"id": "v2", "x": 200, "y": 0}],
            "walls": [{"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
                       "type": "exterior", "openings": openings}],
            "rooms": [], "furnishings": [],
        }
    return doc


def test_features_excludes_opening_stations_from_both_orthogonal_rows():
    """0128-ruling.md sec1: "Doors, windows, and every other opening kind
    leave the dimension stations of every row" -- the bottom X row and
    the left Y row, not just the angled lanes. A door on a wall adds no
    station beyond that wall's own two endpoints."""
    make = _door_wall_doc()
    fx_without, fy_without = _sheet(make(False))._features()
    fx_with, fy_with = _sheet(make(True))._features()
    assert fx_with == fx_without
    assert fy_with == fy_without
    assert len(fx_without) == 2, "expected just the wall's two endpoints"


def test_title_block_notes_openings_are_shown_but_not_dimensioned():
    """0128-ruling.md sec1's own footer instruction: 'openings shown for
    reference; not dimensioned', beside the existing dimension-reference
    note -- so the receiving architect reads the omission as a decision,
    not a gap."""
    src = Path(fp2pdf.__file__).read_text(encoding="utf-8")
    assert "not dimensioned" in src


# ---------------------------------------------------------------------------
# 0120-ruling.md -- tranche 2 item 2: the room-show_dimensions-driven
# angled dimension lane (AMBER)
# ---------------------------------------------------------------------------

def _sheet(doc, level=None):
    return fp2pdf.Sheet(None, doc, level or _MINIMAL_LEVEL,
                         fp2pdf._default_thickness(), False, _MINIMAL_META)


def _triangle_doc(rooms):
    """rooms: [(id, show_dims, x_offset, has_door), ...]. Each room is a
    right triangle (xoff,0)-(xoff+100,0)-(xoff,100): the two legs are
    cardinal (excluded by `_near_cardinal`), the hypotenuse
    (xoff+100,0)-(xoff,100) is the one family edge (45 degrees in
    `Sheet.pt()`'s own y-flipped page space), every room's at the SAME
    angle so same-angle rooms merge into one family (0120-ruling.md
    sec2's own stated consequence)."""
    vertices, walls, room_defs = [], [], []
    for i, (rid, show_dims, xoff, has_door) in enumerate(rooms):
        v0, v1, v2 = f"v{i}0", f"v{i}1", f"v{i}2"
        vertices += [
            {"id": v0, "x": xoff, "y": 0},
            {"id": v1, "x": xoff + 100, "y": 0},
            {"id": v2, "x": xoff, "y": 100},
        ]
        w0, w1, w2 = f"{rid}w0", f"{rid}w1", f"{rid}w2"
        hyp_openings = []
        if has_door:
            hyp_openings = [{"id": f"{rid}o", "kind": "door", "code": "3068",
                             "anchor": {"from": "center", "offset_in": 0.0},
                             "door_type": "LH", "hinge": "v1",
                             "swings_toward": "left"}]
        walls += [
            {"id": w0, "level": "L1", "v1": v0, "v2": v1,
             "type": "exterior", "openings": []},
            {"id": w1, "level": "L1", "v1": v1, "v2": v2,
             "type": "exterior", "openings": hyp_openings},
            {"id": w2, "level": "L1", "v1": v2, "v2": v0,
             "type": "exterior", "openings": []},
        ]
        room_defs.append({
            "id": rid, "level": "L1", "name": rid, "category": "living",
            "area_accounting": "conditioned",
            "outline": [{"v": v0, "wall": w0}, {"v": v1, "wall": w1},
                        {"v": v2, "wall": w2}],
            "label": {"show_dimensions": show_dims},
        })
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [_MINIMAL_LEVEL],
        "vertices": vertices, "walls": walls, "rooms": room_defs,
        "furnishings": [],
    }


@pytest.mark.parametrize("dx,dy,expected", [
    (1.0, 0.0, 0.0), (0.0, 1.0, 90.0), (-1.0, 0.0, 0.0), (1.0, 1.0, 45.0),
])
def test_wall_angle_deg_is_undirected(dx, dy, expected):
    """v1->v2 and v2->v1 must read the same family."""
    assert fp2pdf._wall_angle_deg(dx, dy) == pytest.approx(expected)
    assert fp2pdf._wall_angle_deg(-dx, -dy) == pytest.approx(expected)


@pytest.mark.parametrize("angle,near", [
    (0.0, True), (0.5, True), (179.6, True), (90.0, True), (89.3, True),
    (45.0, False), (135.0, False), (2.0, False), (88.0, False),
])
def test_near_cardinal_excludes_both_axes(angle, near):
    """0120-ruling.md sec2 step 1: near-cardinal is horizontal OR
    vertical -- a wall near 90 degrees is already the Y row's job, same
    as one near 0/180 is the X row's."""
    assert fp2pdf._near_cardinal(angle) is near


def test_angled_families_merges_two_rooms_at_the_same_angle():
    """0120-ruling.md sec2's own stated consequence: all of a family's
    rooms project onto one shared lane."""
    doc = _triangle_doc([("rA", True, 0, False), ("rB", True, 300, False)])
    fams = _sheet(doc)._angled_families()
    assert len(fams) == 1
    # `Sheet.pt()` flips y (Sheet's own "plan coords, y already flipped up"
    # convention), so the hypotenuse's page-space angle is 45, not the
    # 135 its raw (x,y) vertices would suggest -- both rooms land there.
    assert fams[0]["angle"] == pytest.approx(45.0)
    assert {w["id"] for w in fams[0]["walls"]} == {"rAw1", "rBw1"}


def test_angled_families_excludes_a_dims_off_room():
    """0120-ruling.md sec3: a 45 wall in a room with dimensions off gets
    no angled callout -- the feature, not a gap."""
    doc = _triangle_doc([("rA", True, 0, False), ("rB", False, 300, False)])
    fams = _sheet(doc)._angled_families()
    assert len(fams) == 1
    assert {w["id"] for w in fams[0]["walls"]} == {"rAw1"}


def test_angled_families_empty_when_no_room_opts_in():
    doc = _triangle_doc([("rA", False, 0, False)])
    assert _sheet(doc)._angled_families() == []


def test_angled_families_ignores_the_two_cardinal_legs():
    """Only the hypotenuse (45 degrees) is a family member -- the two
    legs are horizontal/vertical, the X/Y rows' own job."""
    doc = _triangle_doc([("rA", True, 0, False)])
    fams = _sheet(doc)._angled_families()
    assert len(fams) == 1
    assert [w["id"] for w in fams[0]["walls"]] == ["rAw1"]


def test_lane_geometry_telescopes_to_the_family_extent():
    """0120-ruling.md sec4's own receipt: a two-room 45 family -> one
    lane, stations telescoping to the family extent -- proven the same
    way 0118-ruling.md's orthogonal rows are, not asserted."""
    doc = _triangle_doc([("rA", True, 0, False), ("rB", True, 300, False)])
    sheet = _sheet(doc)
    fam = sheet._angled_families()[0]
    geo = sheet._lane_geometry(fam)
    stations = geo["stations"]
    assert len(stations) >= 2
    rounded = fp2pdf._rounded_stations(stations)
    segments = sum(b - a for a, b in zip(rounded, rounded[1:], strict=False))
    assert segments == rounded[-1] - rounded[0]


def test_lane_geometry_excludes_door_stations():
    """Patrick's own check on the first cut, against a real plan: "I dont
    want the positions of the doors listed in the dimensions." Overrides
    0119-ruling.md sec1 / 0120-ruling.md sec2 step 3's own instruction to
    include opening centrelines -- a door on the family edge must add NO
    station beyond the wall's own two endpoints. Full trail: 0126-report.md."""
    without_door = _sheet(_triangle_doc([("rA", True, 0, False)]))
    with_door = _sheet(_triangle_doc([("rA", True, 0, True)]))
    fam_no_door = without_door._angled_families()[0]
    fam_door = with_door._angled_families()[0]
    stations_no_door = without_door._lane_geometry(fam_no_door)["stations"]
    stations_with_door = with_door._lane_geometry(fam_door)["stations"]
    assert len(stations_with_door) == len(stations_no_door) == 2, (
        "a door centred on the 135-degree wall added a station of its own")


def test_convert_renders_a_show_dims_angled_room_without_raising(tmp_path):
    pytest.importorskip("reportlab")
    doc = _triangle_doc([("rA", True, 0, True), ("rB", True, 300, False)])
    out = tmp_path / "out.pdf"
    result = convert(doc, out, _MINIMAL_META)
    assert out.exists()
    assert result.warnings == []


def _triangle_plus_distant_wing_doc():
    """A small 45-degree triangle room (the show-dims family, ~140" across
    diagonally) sitting beside a large, FAR AWAY cardinal room -- so the
    overall plan bbox is much bigger than the family's own footprint, the
    shape of Patrick's actual report (docs/evidence/DIM45.png, 0126-report.md):
    a small angled wing on one side of a much larger house. Reproduces the
    bug directly: the first cut sized the lane's clearance off the WHOLE
    bbox and started extension lines from the family's own centroid, so
    they ran hundreds of inches across the big room before reaching the
    lane. A minimal synthetic case; the real corpus regression is
    `test_angled_lane_on_the_real_wiscaway_wing_stays_snug_and_off_the_geometry`."""
    triangle = _triangle_doc([("rA", True, 0, False)])
    far_v0, far_v1, far_v2, far_v3 = "fv0", "fv1", "fv2", "fv3"
    triangle["vertices"] += [
        {"id": far_v0, "x": 2000, "y": 0}, {"id": far_v1, "x": 3000, "y": 0},
        {"id": far_v2, "x": 3000, "y": 1000}, {"id": far_v3, "x": 2000, "y": 1000},
    ]
    triangle["walls"] += [
        {"id": "fw0", "level": "L1", "v1": far_v0, "v2": far_v1,
         "type": "exterior", "openings": []},
        {"id": "fw1", "level": "L1", "v1": far_v1, "v2": far_v2,
         "type": "exterior", "openings": []},
        {"id": "fw2", "level": "L1", "v1": far_v2, "v2": far_v3,
         "type": "exterior", "openings": []},
        {"id": "fw3", "level": "L1", "v1": far_v3, "v2": far_v0,
         "type": "exterior", "openings": []},
    ]
    return triangle


def test_lane_reach_is_local_to_the_family_not_the_whole_plan_bbox():
    """Patrick's second finding: the lane must sit SNUG against the
    family's own outermost wall, not clear across a much larger plan."""
    doc = _triangle_plus_distant_wing_doc()
    sheet = _sheet(doc)
    assert sheet.bx1 - sheet.bx0 > 2500, "fixture must dwarf the triangle"
    fam = sheet._angled_families()[0]
    geo = sheet._lane_geometry(fam)
    # the triangle's own legs run 0..100" -- its outward reach from the
    # hypotenuse should be on that scale, nowhere near the ~3000" bbox
    assert geo["reach"] < 150, (
        f"reach={geo['reach']!r} was pulled out by the far wing's bbox, "
        f"not sized off the family's own footprint")


def test_angled_lane_extension_lines_do_not_cross_the_family_footprint():
    """Patrick's third finding: callouts must not cross over the drawing.
    An extension line runs from the family's own outer edge straight out
    to the lane -- every point on it must be AT OR BEYOND that edge, in
    the outward direction, never back across the family's own walls."""
    doc = _triangle_plus_distant_wing_doc()
    sheet = _sheet(doc)
    fam = sheet._angled_families()[0]
    geo = sheet._lane_geometry(fam)
    n = geo["n"]
    ccx, ccy = geo["ccx"], geo["ccy"]

    def proj_n(x, y):
        return (x - ccx) * n[0] + (y - ccy) * n[1]

    # every member wall's own vertices, in the outward-perpendicular sense,
    # must sit AT OR BEHIND the family's own reach -- nothing pokes past it
    member_n = [proj_n(*sheet.pt(w["v1"])) for w in fam["walls"]]
    member_n += [proj_n(*sheet.pt(w["v2"])) for w in fam["walls"]]
    assert max(member_n) <= geo["reach"] + 1e-6


def test_angled_lane_on_the_real_wiscaway_wing_stays_snug_and_off_the_geometry():
    """The real corpus regression, per fixtures/README.md's own entry --
    Patrick's diagonal wing (SUN/OFFICE/HALL2/UTILITY/MUD/GARAGE), Show
    dimensions forced on, reproduces the first cut's three faults and
    confirms the fix on the actual reported file, not just a synthetic
    triangle."""
    doc = json.loads((Path(__file__).parent.parent / "fixtures" /
                      "wiscaway2026-08-30R1.json").read_text(encoding="utf-8"))
    wing_room_ids = {"r6", "r8", "r13", "r15", "r16", "r22", "r23"}
    for r in doc["rooms"]:
        if r["id"] in wing_room_ids:
            r.setdefault("label", {})["show_dimensions"] = True
    level = next(lv for lv in doc["levels"] if lv["id"] == "L1")
    sheet = _sheet(doc, level)
    families = sheet._angled_families()
    assert len(families) == 2, "expected the two wing runs (~45 / ~135)"
    for fam in families:
        geo = sheet._lane_geometry(fam)
        n = geo["n"]
        ccx, ccy = geo["ccx"], geo["ccy"]
        # snug: the reach stays on the wing's own scale, nowhere near the
        # ~1360" whole-plan bbox this fixture's house spans
        assert geo["reach"] < 500
        # no crossing: no member wall pokes past the lane's own reach
        member_n = [(sheet.pt(w["v1"])[0] - ccx) * n[0]
                    + (sheet.pt(w["v1"])[1] - ccy) * n[1]
                    for w in fam["walls"]]
        member_n += [(sheet.pt(w["v2"])[0] - ccx) * n[0]
                     + (sheet.pt(w["v2"])[1] - ccy) * n[1]
                     for w in fam["walls"]]
        assert max(member_n) <= geo["reach"] + 1e-6
        # no door stations: this fixture is only a meaningful regression
        # for the omission if at least one wing wall actually carries an
        # opening, and RAW (pre-cluster) stations must be exactly the two
        # endpoints per wall -- never more, however many openings exist
        assert any(w.get("openings") for w in fam["walls"]), (
            "fixture no longer carries an opening on the wing -- "
            "the door-omission receipt needs one to mean anything")
        assert len(geo["stations"]) <= 2 * len(fam["walls"])


# ---------------------------------------------------------------------------
# 0129-ruling.md sec3(a)/(c) -- grid-aware station filtering, the
# document's own wall_snap_in, and the centerline title-block note
# ---------------------------------------------------------------------------

def test_grid_filter_stations_drops_the_off_grid_member_of_a_close_pair():
    """24.0 is a 6" grid multiple; 24.3 is not, and sits 0.3" away --
    well under the 6" grid step. The off-grid one goes."""
    assert fp2pdf.grid_filter_stations([24.0, 24.3], 6.0) == [24.0]


def test_grid_filter_stations_keeps_an_all_off_grid_crowds_mean():
    """Neither 24.3 nor 24.6 is on-grid -- nothing to prefer, so
    clustering's own mean stands, unchanged."""
    out = fp2pdf.grid_filter_stations([24.3, 24.6], 6.0)
    assert out == [pytest.approx((24.3 + 24.6) / 2)]


def test_grid_filter_stations_never_drops_a_lone_grid_station():
    out = fp2pdf.grid_filter_stations([6.0], 6.0)
    assert out == [6.0]


def test_grid_filter_stations_leaves_far_apart_stations_alone():
    """8" apart is >= the 6" grid step -- not a crowd, not filtered."""
    assert fp2pdf.grid_filter_stations([24.0, 32.0], 6.0) == [24.0, 32.0]


def test_grid_filter_uses_the_snap_value_given_not_a_hardcoded_six():
    """The same 8"-apart pair as above, but a 12" grid step now makes
    them a crowd -- and only 24.0 (a multiple of 12) is on-grid. A
    receipt that passes with either value proves nothing (0132-ruling.md
    sec2); this one only passes because the function actually reads
    `snap_in`."""
    assert fp2pdf.grid_filter_stations([24.0, 32.0], 12.0) == [24.0]


def test_sheet_wall_snap_in_defaults_to_six_when_settings_missing():
    sheet = _sheet(_rect_doc())
    assert sheet.wall_snap_in == 6.0


def test_sheet_wall_snap_in_is_read_from_the_documents_settings():
    doc = _rect_doc()
    doc["settings"] = {"wall_snap_in": 12.0}
    sheet = _sheet(doc)
    assert sheet.wall_snap_in == 12.0


def test_dim_note_defaults_say_centerlines_not_faces():
    """0129-ruling.md sec3(c): the old faces doctrine is superseded by
    its author. Checked in both places the note text lives -- the CLI
    default and the PDF export dialog's default -- so neither reverts
    silently."""
    fp2pdf_src = Path(fp2pdf.__file__).read_text(encoding="utf-8")
    assert "All dimensions to wall centerlines" in fp2pdf_src
    assert "overall wall faces" not in fp2pdf_src
    dialogs_path = Path(fp2pdf.__file__).resolve().parent.parent / "dialogs.py"
    dialogs_src = dialogs_path.read_text(encoding="utf-8")
    assert "All dimensions to wall centerlines" in dialogs_src
    assert "overall wall faces" not in dialogs_src


def test_features_and_lane_geometry_never_apply_a_face_offset():
    """0129-ruling.md sec3(c): stations already come from vertex
    (centerline) coordinates -- a source guard against a face offset
    creeping into either function later."""
    import inspect
    for fn in (fp2pdf.Sheet._features, fp2pdf.Sheet._lane_geometry):
        src = inspect.getsource(fn)
        assert "wall_t" not in src
        assert "self.th" not in src


def test_lane_labels_have_no_fractional_remainder():
    """0129-ruling.md sec3(b): the 45/135 lanes label in the same
    whole-inch feet-and-inches form the orthogonal rows use -- confirmed,
    not assumed. `ftin` only appends a "n/d" suffix when there IS a
    fraction, so its absence proves the whole-inch rounding reached the
    lane's own labels too."""
    doc = _triangle_doc([("rA", True, 0, False), ("rB", True, 300, False)])
    sheet = _sheet(doc)
    fam = sheet._angled_families()[0]
    geo = sheet._lane_geometry(fam)
    rounded = fp2pdf._rounded_stations(geo["stations"])
    assert len(rounded) >= 2
    for ra, rb in zip(rounded, rounded[1:], strict=False):
        assert "/" not in fp2pdf.ftin(rb - ra)


# ---------------------------------------------------------------------------
# 0130-ruling.md -- family exclusivity: a wall's endpoints go only to the
# row family matching its own angle
# ---------------------------------------------------------------------------

def test_features_excludes_a_lone_diagonal_walls_endpoints():
    """A doc with exactly one wall, at 45 degrees, and no cardinal walls
    at all: `_features()` must come back empty. Before 0130, every
    wall's endpoints went into both fx and fy regardless of angle -- this
    is RED against that code, by construction (0080-report.md's own
    telescoping-contrast precedent: proven by arithmetic, not a revert)."""
    doc = {
        "format": "floorplanner-design", "version": 5,
        "levels": [_MINIMAL_LEVEL],
        "vertices": [{"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 100, "y": 100}],
        "walls": [{"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
                   "type": "exterior", "openings": []}],
        "rooms": [], "furnishings": [],
    }
    fx, fy = _sheet(doc)._features()
    assert fx == []
    assert fy == []


def _shared_corner_doc():
    """v1(0,0)-v2(100,0): a cardinal wall. v2(100,0)-v3(150,50): a 45
    degree wall sharing v2 with the cardinal one. v3 belongs to no
    cardinal wall at all."""
    return {
        "format": "floorplanner-design", "version": 5,
        "levels": [_MINIMAL_LEVEL],
        "vertices": [{"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 100, "y": 0},
                     {"id": "v3", "x": 150, "y": 50}],
        "walls": [
            {"id": "w1", "level": "L1", "v1": "v1", "v2": "v2",
             "type": "exterior", "openings": []},
            {"id": "w2", "level": "L1", "v1": "v2", "v2": "v3",
             "type": "exterior", "openings": []},
        ],
        "rooms": [{"id": "r1", "level": "L1", "name": "R", "category": "living",
                   "area_accounting": "conditioned",
                   "outline": [{"v": "v1", "wall": "w1"},
                               {"v": "v2", "wall": "w2"},
                               {"v": "v3", "wall": None}],
                   "label": {"show_dimensions": True}}],
        "furnishings": [],
    }


def test_shared_corner_appears_in_both_families_once_each():
    """0130-ruling.md sec1: "a shared corner between an orthogonal and a
    45 wall appears in both families -- once from each wall, at the same
    point -- which is correct, not a duplicate." v2 is that corner; v3
    belongs only to the diagonal wall and must be absent from the X/Y
    rows entirely."""
    doc = _shared_corner_doc()
    sheet = _sheet(doc)
    fx, fy = sheet._features()
    v1, v2, v3 = sheet.pt("v1"), sheet.pt("v2"), sheet.pt("v3")
    assert any(abs(x - v2[0]) < 1e-6 for x in fx), "the shared corner is missing from the X row"
    assert any(abs(x - v1[0]) < 1e-6 for x in fx), "the cardinal wall's own far end is missing"
    assert not any(abs(x - v3[0]) < 1e-6 for x in fx), (
        "the diagonal-only vertex leaked into the X row")
    fams = sheet._angled_families()
    assert len(fams) == 1
    geo = sheet._lane_geometry(fams[0])

    def proj(p):
        return ((p[0] - geo["ccx"]) * geo["u"][0]
                 + (p[1] - geo["ccy"]) * geo["u"][1])

    assert any(abs(s - proj(v2)) < 1e-6 for s in geo["stations"]), (
        "the shared corner is missing from its own lane")
    assert any(abs(s - proj(v3)) < 1e-6 for s in geo["stations"])


def test_real_wiscaway_r2_wing_vertex_is_absent_from_the_orthogonal_rows():
    """The real corpus corroboration, per 0130-ruling.md sec3's own
    receipt list -- run against the file 0132-ruling.md names as the
    tranche's baseline, whose show_dimensions flags are already set as
    Patrick left them (no forcing needed)."""
    doc = json.loads((Path(__file__).parent.parent / "fixtures" /
                      "wiscaway2026-08-30R2.json").read_text(encoding="utf-8"))
    level = next(lv for lv in doc["levels"] if lv["id"] == "L1")
    sheet = _sheet(doc, level)
    fams = sheet._angled_families()
    assert fams, "expected at least one angled family on the real wing"
    fx, fy = sheet._features()
    assert fx and fy
    w = fams[0]["walls"][0]
    p1 = sheet.pt(w["v1"])
    assert not any(abs(x - p1[0]) < 1e-6 for x in fx), (
        "an angled-wing vertex leaked into the X row on the real file")
    assert not any(abs(y - p1[1]) < 1e-6 for y in fy), (
        "an angled-wing vertex leaked into the Y row on the real file")
