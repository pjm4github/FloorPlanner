"""Plain "Snap to Grid" -- 0108-ruling.md, amended by 0109-ruling.md SS3.

Both of a wall's endpoints snap to the nearest grid point INDEPENDENTLY --
NOT the orthogonality repair (a wall can be axis-aligned and off-grid, or
the reverse, 0108 SS1) and NOT `snap_wall_to_grid_orthogonal` (no anchor,
no shared axis, no near-45 hazard: whichever angle the wall ends up at is
whatever the two independently-rounded ends produce, not forced onto axis).
"""
import pytest

from floorplanner.design.validate import (
    check,
    snap_wall_to_grid,
    wall_angle_deviation_deg,
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
# the happy path -- both ends land on grid, independently
# ---------------------------------------------------------------------------

def test_both_ends_snap_to_the_nearest_grid_point_independently():
    doc = _doc(
        vertices=[_v("v1", 79.03, 50.0), _v("v2", 78.94, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] is None
    assert _xy(res["doc"], "v1") == (78.0, 48.0)
    assert _xy(res["doc"], "v2") == (78.0, 102.0)


def test_a_wall_that_straddles_a_grid_line_can_come_out_tilted():
    """0110-ruling.md SS2's own finding about this action: independent
    rounding is the hazard the orthogonal variant exists to avoid -- this
    fixture is the exact shape that produces it, confirmed here rather than
    only asserted in the ruling."""
    doc = _doc(
        vertices=[_v("v1", 80.9, 0.0), _v("v2", 81.1, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] is None
    ax, _ay = _xy(res["doc"], "v1")
    bx, _by = _xy(res["doc"], "v2")
    assert ax != bx                          # tilted -- no longer vertical


def test_relocations_name_only_the_vertices_that_actually_moved():
    doc = _doc(
        vertices=[_v("v1", 78.0, 48.0), _v("v2", 78.94, 100.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] is None
    assert len(res["relocations"]) == 1


def test_a_wall_already_exactly_on_grid_produces_no_relocations():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 0.0, 120.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] is None
    assert res["relocations"] == []


# ---------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------

def test_a_degenerate_result_is_refused_and_nothing_is_applied():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 2.0, 1.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] == "degenerate"
    assert res["doc"] is doc
    assert res["relocations"] == []


def test_an_opening_that_would_run_off_the_shrunk_wall_is_refused():
    """Same fixture shape as the orthogonal variant's own test -- the wall
    shrinks from ~8.06in to 6in; a 7in-wide opening anchored at v1 fits
    before and not after."""
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 8.0, 1.0)],
        walls=[_w("w1", "v1", "v2", openings=[{
            "id": "o1", "kind": "window", "code": "0780",
            "anchor": {"from": "v1", "offset_in": 0.0}}])],
    )
    before = check(doc, deep=True)
    assert not any(m.startswith("I7") for m in before)
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] == "would introduce I7"
    assert res["doc"] is doc


def test_a_pre_existing_violation_elsewhere_does_not_block_the_snap():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 0.0, 120.0),
                  _v("v3", 200.0, 0.0), _v("v4", 210.0, 0.0)],
        walls=[_w("w1", "v1", "v2"),
               _w("w2", "v3", "v4", openings=[{
                   "id": "o1", "kind": "window", "code": "3040",
                   "anchor": {"from": "v1", "offset_in": 0.0}}])],
    )
    before = check(doc, deep=True)
    assert any(m.startswith("I7") for m in before)
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] is None


# ---------------------------------------------------------------------------
# 0109-ruling.md SS3: a worsened neighbour is REPORTED, not refused
# ---------------------------------------------------------------------------

def test_a_worsened_shared_neighbour_is_reported_not_refused():
    doc = _doc(
        vertices=[_v("vZ", -100.0, 50.0), _v("v1", 79.03, 50.0),
                  _v("v2", 78.94, 100.0)],
        walls=[_w("wZ", "vZ", "v1"),           # exactly horizontal, shares v1
               _w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] is None
    assert "wZ" in res["worsened"]
    assert _xy(res["doc"], "v1") == (78.0, 48.0)


def test_no_worsening_reports_an_empty_list():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 0.0, 120.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["worsened"] == []


# ---------------------------------------------------------------------------
# no near-45 refusal -- unlike the orthogonal variant, nothing here forces
# an axis, so a diagonal wall is simply left diagonal
# ---------------------------------------------------------------------------

def test_a_near_45_degree_wall_is_not_refused_on_that_ground():
    doc = _doc(
        vertices=[_v("v1", 0.0, 0.0), _v("v2", 100.0, 99.0)],
        walls=[_w("w1", "v1", "v2")],
    )
    deg_before = wall_angle_deviation_deg((0.0, 0.0), (100.0, 99.0))
    res = snap_wall_to_grid(doc, "w1", step=6.0)
    assert res["refused"] is None
    ax, ay = _xy(res["doc"], "v1")
    bx, by = _xy(res["doc"], "v2")
    deg_after = wall_angle_deviation_deg((ax, ay), (bx, by))
    assert deg_before > 0.0 and deg_after > 0.0   # stayed a diagonal
