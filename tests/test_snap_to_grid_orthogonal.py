"""Snap to Grid Orthogonal -- 0110-ruling.md SS2, amended by 0109-ruling.md
SS3.

The clicked vertex anchors: it snaps to the nearest grid point on both
coordinates. The other vertex takes the clicked vertex's SHARED-AXIS
coordinate (whichever must match for the wall to land exactly on axis,
chosen by the wall's larger original delta) and its own free coordinate
independently snaps to grid. Result: exactly axis-aligned AND both ends on
grid, in one move -- NOT `repair_wall_orthogonality` (0108-ruling.md SS1: a
wall can be perfectly axis-aligned and badly off-grid, or the reverse).

Refusals (0108-ruling.md SS3, amended by 0109-ruling.md SS3): a degenerate
result, a wall too near 45 degrees to have a shared axis, or a NEW
check() violation (the same stable-key interlock the batch repair uses) --
all refuse. A neighbour's angle or grid error getting WORSE is only
REPORTED, per 0109's amendment; it is not a refusal.
"""
import math

import pytest

from floorplanner.design.validate import (
    check,
    snap_wall_to_grid_orthogonal,
    vertex_grid_error_in,
    wall_angle_deviation_deg,
    wall_grid_error_in,
    SNAP_ORTHO_NEAR_45_DEG,
)

pytestmark = pytest.mark.walls


def _doc(vertices, walls, level="L1"):
    return {
        "levels": [{"id": level, "name": "Level", "elevation_in": 0}],
        "vertices": vertices, "walls": walls,
        "rooms": [], "furnishings": [], "groups": [],
    }


def _v(vid, x, y, level="L1"):
    return {"id": vid, "level": level, "x": x, "y": y}


def _w(wid, v1, v2, level="L1", type_="interior", openings=None):
    row = {"id": wid, "v1": v1, "v2": v2, "level": level, "type": type_}
    if openings:
        row["openings"] = openings
    return row


def _xy(doc, vid):
    return next((v["x"], v["y"]) for v in doc["vertices"] if v["id"] == vid)


# ---------------------------------------------------------------------------
# vertex_grid_error_in / wall_grid_error_in -- the raw measurement
# ---------------------------------------------------------------------------

def test_vertex_grid_error_is_zero_exactly_on_grid():
    assert vertex_grid_error_in(78.0, 48.0, 6.0) == 0.0


def test_vertex_grid_error_is_positive_off_grid():
    err = vertex_grid_error_in(79.03, 50.0, 6.0)
    assert err > 0.0
    assert err == pytest.approx(math.hypot(79.03 - 78.0, 50.0 - 48.0))


def test_wall_grid_error_is_the_worse_of_the_two_endpoints():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 6.02, 0.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    errs = wall_grid_error_in(doc, 6.0)
    assert errs["w1"] == pytest.approx(0.02)


# ---------------------------------------------------------------------------
# the happy path -- exactly axis-aligned AND both ends on grid
# ---------------------------------------------------------------------------

def test_a_near_vertical_wall_snaps_to_exactly_vertical_and_on_grid():
    """Clicked v1 anchors; the wall runs mostly in y, so the SHARED axis is
    x -- the other vertex takes the clicked vertex's new x."""
    doc = _doc(
        vertices=[_v("v1", 79.03, 50.0), _v("v2", 78.94, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] is None
    ax, ay = _xy(res["doc"], "v1")
    bx, by = _xy(res["doc"], "v2")
    assert (ax, ay) == (78.0, 48.0)          # nearest grid, both coordinates
    assert bx == ax                          # shared axis: exactly vertical
    assert by == 102.0                       # its own free coordinate, snapped
    assert wall_angle_deviation_deg((ax, ay), (bx, by)) == 0.0


def test_a_near_horizontal_wall_snaps_to_exactly_horizontal_and_on_grid():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 60.0, 1.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] is None
    ax, ay = _xy(res["doc"], "v1")
    bx, by = _xy(res["doc"], "v2")
    assert (ax, ay) == (0.0, 0.0)
    assert by == ay                          # shared axis: exactly horizontal
    assert bx == 60.0                        # its own free coordinate, snapped


def test_clicking_the_OTHER_end_anchors_there_instead():
    """The anchor is whichever vertex was clicked -- not always v1."""
    doc = _doc(
        vertices=[_v("v1", 79.03, 50.0), _v("v2", 78.94, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v2", step=6.0)
    assert res["refused"] is None
    ax, ay = _xy(res["doc"], "v1")
    bx, by = _xy(res["doc"], "v2")
    assert (bx, by) == (78.0, 102.0)         # v2 is now the anchor
    assert ax == bx
    assert ay == 48.0                        # v1's own free coordinate, snapped


def test_relocations_name_both_moved_vertices():
    doc = _doc(
        vertices=[_v("v1", 79.03, 50.0), _v("v2", 78.94, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert len(res["relocations"]) == 2
    levels = {r[0] for r in res["relocations"]}
    assert levels == {"L1"}


def test_a_vertex_already_exactly_on_its_target_produces_no_relocation_for_it():
    """Only the vertex that actually MOVED gets a relocation entry -- if the
    clicked end is already exactly on grid, it contributes none."""
    doc = _doc(
        vertices=[_v("v1", 78.0, 48.0), _v("v2", 78.94, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] is None
    assert len(res["relocations"]) == 1


# ---------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------

def test_a_degenerate_result_is_refused_and_nothing_is_applied():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 2.0, 1.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] == "degenerate"
    assert res["doc"] is doc
    assert res["relocations"] == []


def test_a_wall_near_45_degrees_is_refused():
    """A near-perfect diagonal has no larger delta to choose an axis by."""
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 100.0, 99.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    deg = wall_angle_deviation_deg((0.0, 0.0), (100.0, 99.0))
    assert deg > 45.0 - SNAP_ORTHO_NEAR_45_DEG          # confirms the fixture
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] == "near-45"
    assert res["doc"] is doc


def test_a_wall_comfortably_off_45_is_not_refused_on_that_ground():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 60.0, 1.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] is None


def test_an_opening_that_would_run_off_the_shrunk_wall_is_refused():
    """The wall shrinks from ~8.06in to 6in; a 7in-wide opening anchored at
    the fixed end fits before and not after -- a NEW I7 violation, caught by
    the same check()-differential interlock the batch repair uses."""
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 8.0, 1.0)],
        walls=[_w("w1", "v1", "v2", openings=[{
            "id": "o1", "kind": "window", "code": "0780",
            "anchor": {"from": "v1", "offset_in": 0.0}}])],
    )
    before = check(doc, deep=True)
    assert not any(m.startswith("I7") for m in before)   # fits originally
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] == "would introduce I7"
    assert res["doc"] is doc
    assert res["relocations"] == []


def test_a_pre_existing_I7_violation_elsewhere_does_not_block_the_snap():
    """0082-ruling.md's interlock, reused: a document that already fails
    check() (an unrelated wall's opening hangs off) still lets an
    unconnected wall snap -- only a NEW violation refuses."""
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 60.0, 1.0),
                  _v("v3", 200.0, 0.0), _v("v4", 210.0, 0.0)],
        walls=[_w("w1", "v1", "v2"),
               _w("w2", "v3", "v4", openings=[{
                   "id": "o1", "kind": "window", "code": "3040",
                   "anchor": {"from": "v1", "offset_in": 0.0}}])],
    )
    before = check(doc, deep=True)
    assert any(m.startswith("I7") for m in before)        # pre-existing
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] is None


# ---------------------------------------------------------------------------
# 0109-ruling.md SS3: a worsened neighbour is REPORTED, not refused
# ---------------------------------------------------------------------------

def test_a_worsened_shared_neighbour_is_reported_not_refused():
    """v1 is shared with wZ, exactly on axis before the snap. Moving v1's y
    (its own free coordinate rounds away from wZ's) tilts wZ off axis --
    still applied, wZ named in `worsened`."""
    doc = _doc(
        vertices=[_v("vZ", -100.0, 50.0), _v("v1", 79.03, 50.0),
                  _v("v2", 78.94, 100.0)],
        walls=[_w("wZ", "vZ", "v1"),           # exactly horizontal, shares v1
               _w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] is None
    assert "wZ" in res["worsened"]
    # and it really did move -- not merely flagged
    assert _xy(res["doc"], "v1") == (78.0, 48.0)


def test_no_worsening_reports_an_empty_list():
    doc = _doc(
        vertices=[_v("v1", 79.03, 50.0), _v("v2", 78.94, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["worsened"] == []


# ---------------------------------------------------------------------------
# shared-vertex identity -- moving a corner moves every wall that holds it
# ---------------------------------------------------------------------------

def test_a_shared_vertex_moves_every_wall_that_holds_it():
    """`v1` is `wZ`'s far end AND `w1`'s clicked/anchor end -- the SAME
    document vertex id, so `wZ` reads whatever `v1` ends up at without any
    code here touching `wZ` directly (P3.1's identity-carrying relocation)."""
    doc = _doc(
        vertices=[_v("vZ", -100.0, 0.02), _v("v1", 79.03, 50.0),
                  _v("v2", 78.94, 100.0)],
        walls=[_w("wZ", "vZ", "v1"), _w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid_orthogonal(doc, "w1", "v1", step=6.0)
    assert res["refused"] is None
    zw = next(w for w in res["doc"]["walls"] if w["id"] == "wZ")
    assert zw["v1"] == "v1" or zw["v2"] == "v1"
    assert _xy(res["doc"], "v1") == (78.0, 48.0)
