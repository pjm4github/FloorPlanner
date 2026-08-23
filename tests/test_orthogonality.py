"""Wall orthogonality report -- 0055-ruling.md item B (a REPORT, not a
repair). Item C, the repair, is `test_orthogonality_repair.py`.

Grid snap constrains new cursor input; it cannot see a wall an existing
operation (move/join/weld/coalesce) already rotated off axis, and this
measures exactly that population -- deviation in degrees from the nearest
axis-aligned angle, per wall, with no judgement about which are deliberate
diagonals and which are drift (the ruling declines that question, SS5).

Calls the production functions (`wall_angle_deviation_deg`,
`wall_orthogonality`, `orthogonality_bands`) rather than restating the
math, per this project's own rule.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp
from floorplanner.design.validate import (
    ORTHOGONALITY_BANDS, orthogonality_bands, wall_angle_deviation_deg,
    wall_orthogonality, wall_orthogonality_displacement_in,
)

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parent.parent


def _doc(walls, vertices):
    """A minimal v5-shaped document -- just enough for `wall_orthogonality`
    to read (`vertices`, `walls`), not a schema-valid document."""
    return {"vertices": vertices, "walls": walls}


def _v(vid, x, y):
    return {"id": vid, "x": x, "y": y}


def _w(wid, v1, v2, level="L1", type_="interior"):
    return {"id": wid, "v1": v1, "v2": v2, "level": level, "type": type_}


# ---------------------------------------------------------------------------
# wall_angle_deviation_deg -- the raw math
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("a,b,expect", [
    ((0, 0), (100, 0), 0.0),          # due east: exactly on axis
    ((0, 0), (0, 100), 0.0),          # due north: exactly on axis
    ((0, 0), (-100, 0), 0.0),         # due west: exactly on axis
    ((0, 0), (0, -100), 0.0),         # due south: exactly on axis
    ((0, 0), (100, 100), 45.0),       # a perfect 45-degree diagonal
    ((0, 0), (-100, 100), 45.0),      # the other diagonal
])
def test_axis_and_diagonal_walls_read_exactly(a, b, expect):
    """THE POSITIVE CONTROL FOR ZERO: an instrument that always reports 0
    is indistinguishable from a broken one unless a non-zero case is also
    demonstrated (the positive-control family, WORKING_AGREEMENT.md) --
    both are driven here, in one table."""
    assert wall_angle_deviation_deg(a, b) == pytest.approx(expect, abs=1e-9)


def test_a_small_drift_reads_as_a_small_positive_number():
    """A wall almost, but not quite, on axis -- the exact shape 0055 SS2
    calls "the class that makes a CAD tool complain about walls which look
    perfectly straight to the person who drew them"."""
    deg = wall_angle_deviation_deg((0, 0), (100, 0.5))
    assert 0.0 < deg < 1.0


def test_a_degenerate_wall_reads_zero_rather_than_crashing():
    """A coincident vertex pair has no defined angle; I3 already flags it
    as invalid elsewhere, so this reports 0 rather than raising -- this
    report is about VALID walls, not a second copy of `check()`."""
    assert wall_angle_deviation_deg((5, 5), (5, 5)) == 0.0


def test_deviation_is_symmetric_regardless_of_wall_direction():
    """v1->v2 and v2->v1 are the same wall; the report must not depend on
    which vertex happens to be recorded first."""
    a, b = (0, 0), (100, 0.5)
    assert wall_angle_deviation_deg(a, b) == pytest.approx(
        wall_angle_deviation_deg(b, a), abs=1e-9)


# ---------------------------------------------------------------------------
# wall_orthogonality_displacement_in -- 0066-ruling.md sec1: the repair's
# tolerance is a DISPLACEMENT, not a degree
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deg,length_in,expect", [
    (0.0002, 450.00, 0.002),
    (0.6488, 90.01, 1.019),
    (0.9094, 63.01, 1.000),
    (0.9290, 185.02, 3.000),
])
def test_displacement_matches_0066s_own_four_row_table(deg, length_in, expect):
    """Cross-checked against 0066-ruling.md sec1's own printed table rather
    than trusted -- the two nearly-identical-angle rows (0.9094deg/1.000in,
    0.9290deg/3.000in) are the ruling's own argument that a degree cut
    cannot bound a repair; reproducing them independently is the receipt
    that this implementation makes the same argument, not a different
    one."""
    got = wall_orthogonality_displacement_in(deg, length_in)
    assert got == pytest.approx(expect, abs=5e-4)


def test_displacement_is_zero_exactly_on_axis():
    assert wall_orthogonality_displacement_in(0.0, 450.0) == 0.0


# ---------------------------------------------------------------------------
# wall_orthogonality -- per-document, sorted worst-first, skips bad refs
# ---------------------------------------------------------------------------

def test_wall_orthogonality_sorts_worst_first_and_skips_missing_vertices():
    doc = _doc(
        walls=[
            _w("w1", "v1", "v2"),              # on axis: 0.0
            _w("w2", "v3", "v4"),              # small drift
            _w("w3", "v5", "v6"),              # 45 degrees
            _w("w4", "v1", "vMISSING"),        # I2 violation elsewhere: skip
        ],
        vertices=[
            _v("v1", 0, 0), _v("v2", 100, 0),
            _v("v3", 0, 50), _v("v4", 100, 50.5),
            _v("v5", 0, 100), _v("v6", 100, 200),
        ],
    )
    rows = wall_orthogonality(doc)
    ids = [r[0] for r in rows]
    assert ids == ["w3", "w2", "w1"]           # 45deg, then drift, then 0
    assert "w4" not in ids                     # missing vertex: skipped, not crashed
    assert rows[0][1] == "L1" and rows[0][2] == "interior"    # level/type carried through


def test_wall_orthogonality_on_an_ALL_AXIS_document_is_the_negative_control():
    """Every wall exactly on axis -- the report must find nothing, and this
    is the negative half of the control pair (the positive half is the
    parametrized 45-degree case above and the corpus check below)."""
    doc = _doc(
        walls=[_w("w1", "v1", "v2"), _w("w2", "v2", "v3")],
        vertices=[_v("v1", 0, 0), _v("v2", 100, 0), _v("v3", 100, 100)],
    )
    rows = wall_orthogonality(doc)
    assert all(deg == 0.0 for _wid, _lvl, _typ, deg, _disp in rows)
    assert all(disp == 0.0 for *_rest, disp in rows)


# ---------------------------------------------------------------------------
# orthogonality_bands -- bucketing, zero-filled
# ---------------------------------------------------------------------------

def test_bands_are_zero_filled_even_when_empty():
    """An instrument that only prints non-empty bands cannot be told apart
    from one that never ran -- the positive-control family again, applied
    to the census rather than the measurement."""
    bands = orthogonality_bands([])
    assert bands == {label: 0 for _lo, _hi, label in ORTHOGONALITY_BANDS}


def test_bands_sort_each_row_into_exactly_one_band():
    rows = [
        ("w1", "L1", "interior", 10.0, 1.0),    # > 5
        ("w2", "L1", "interior", 3.0, 1.0),     # 1-5
        ("w3", "L1", "interior", 0.5, 1.0),     # 0.1-1
        ("w4", "L1", "interior", 0.05, 1.0),    # 0.01-0.1
        ("w5", "L1", "interior", 0.0, 0.0),     # < 0.01 (exactly zero)
        ("w6", "L1", "interior", 0.005, 1.0),   # < 0.01
    ]
    bands = orthogonality_bands(rows)
    assert bands["> 5 deg"] == 1
    assert bands["1-5 deg"] == 1
    assert bands["0.1-1 deg"] == 1
    assert bands["0.01-0.1 deg"] == 1
    assert bands["on axis"] == 1
    assert bands["0 < dev < 0.01 deg"] == 1
    assert sum(bands.values()) == len(rows)


# ---------------------------------------------------------------------------
# corpus receipt -- the census 0055 SS2 says nobody has ever run
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,expect_offaxis", [
    ("examples/planc1.v5.json", 6),
    ("examples/symmetricP1.json", 2),
])
def test_the_corpus_receipt_matches_0055s_own_measurement(name, expect_offaxis):
    """0055-ruling.md SS2: "planc1.v5.json carries 6 walls at 0.0666deg;
    symmetricP1.json carries 2." Cross-checked here against this
    implementation rather than trusted -- a second, independent instrument
    agreeing with the first is stronger evidence than either alone."""
    doc = json.loads((ROOT / name).read_text(encoding="utf-8"))
    rows = wall_orthogonality(doc)
    offaxis = [r for r in rows if r[3] > 0.0]
    assert len(offaxis) == expect_offaxis, [r[:1] + r[3:] for r in offaxis]
    # every one of these corpus deviations is sub-0.1 degree -- none belong
    # in the two worst bands, matching 0055's own reading of drift vs
    # architecture
    bands = orthogonality_bands(rows)
    assert bands["> 5 deg"] == 0
    assert bands["1-5 deg"] == 0


# ---------------------------------------------------------------------------
# the dialog -- a thin smoke test; the math above is where the coverage is
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_the_dialog_lists_an_off_axis_wall_it_is_given(win):
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(200, 3), "interior"))
    dlg = fp.OrthogonalityReportDialog(win)
    try:
        assert dlg.listw.count() == 1
        assert "off axis" in dlg.info.text()
    finally:
        dlg.close()


@pytest.mark.gui
def test_the_dialog_reports_clean_when_every_wall_is_on_axis(win):
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(200, 0), "interior"))
    dlg = fp.OrthogonalityReportDialog(win)
    try:
        assert dlg.listw.count() == 0
        assert "axis-aligned" in dlg.info.text()
    finally:
        dlg.close()
