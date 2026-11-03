"""The per-END overhang (`end_overhang_in`) -- the rake overhang past a
gable end, and a dormer's FACE eave at its own end. A general, additive,
optional `[end0, end1]` field on every roof (not dormer-only); the plane
continues flat past a gable end, so the ridge holds its height out to the
rake and only the painted eaves and the gable line reach further. Phase 1:
the model, the schema, the geometry and the round trip -- grips, the dialog
and the solid-wall rendering come later.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.validate import schema_errors
from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.walls


def _doc(roofs):
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [],
            "groups": [], "roofs": list(roofs)}


def _roof(rid="rf1", **kw):
    r = {"id": rid, "level": "L1", "ridge": [[0.0, 100.0], [200.0, 100.0]], "eaves_h_in": 96.0,
         "ridge_h_in": 132.0, "overhang_in": [0.0, 0.0], "span_in": [100.0, 100.0],
         "eaves_bind": "manual", "gable": [True, True], "marker_end": 1}
    r.update(kw)
    return r


# -- the item ---------------------------------------------------------------
def test_the_default_is_zero_both_ends_and_normalises_like_the_other_pairs():
    rf = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=100.0)
    assert rf.end_overhang_in == [0.0, 0.0]
    rf.end_overhang_in = 18.0                     # a bare number sets both
    assert rf.end_overhang_in == [18.0, 18.0]
    rf.end_overhang_in = [24.0, 0.0]
    assert rf.end_overhang_in == [24.0, 0.0]
    rf.end_overhang_in = [-5.0, 10.0]             # non-negative
    assert rf.end_overhang_in == [0.0, 10.0]
    rf.end_overhang_in = None                     # None resets to zero
    assert rf.end_overhang_in == [0.0, 0.0]


def test_a_gable_ends_overhang_pushes_its_eaves_and_gable_line_out():
    # ridge p1=(0,100) -> p2=(200,100); the axis is +x. end0 is at p1.
    rf = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=100.0,
                  overhang_in=0.0, end_overhang_in=[24.0, 0.0])
    e1a, e1b, e2a, e2b = rf._eave_ends()
    # end0 (p1 side) eaves are pushed 24in OUT along -x, past the ridge end
    assert e1a.x() == pytest.approx(-24.0) and e2a.x() == pytest.approx(-24.0)
    # end1 (p2 side) is untouched -- its own overhang is 0
    assert e1b.x() == pytest.approx(200.0) and e2b.x() == pytest.approx(200.0)


def test_a_hip_end_ignores_the_end_overhang():
    # end0 a hip: it has its own run; the rake overhang does not apply there
    rf = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=100.0,
                  overhang_in=0.0, gable=[False, True], end_overhang_in=[24.0, 0.0])
    e1a, _, e2a, _ = rf._eave_ends()
    # the hip push is the mean span (100), NOT 100 + 24
    assert e1a.x() == pytest.approx(-100.0) and e2a.x() == pytest.approx(-100.0)


def test_the_surface_height_is_unchanged_a_flat_plane_continues_past_the_rake():
    from floorplanner.roofclip import Pt, surface_height
    plain = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=100.0,
                     eaves_h_in=96.0, ridge_h_in=132.0)
    raked = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=100.0,
                     eaves_h_in=96.0, ridge_h_in=132.0, end_overhang_in=[24.0, 0.0])
    # on the ridge line, 12in out past end0 (into the rake): the ridge holds
    for r in (plain, raked):
        assert surface_height(r, Pt(-12.0, 100.0)) == pytest.approx(132.0)
    # mid-slope, 12in out: both the same (the plane simply continues)
    assert surface_height(raked, Pt(-12.0, 150.0)) == pytest.approx(
        surface_height(plain, Pt(-12.0, 150.0)))


def test_the_geometry_key_distinguishes_the_end_overhang():
    a = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=100.0)
    b = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=100.0,
                 end_overhang_in=[24.0, 0.0])
    assert a.geometry_key() != b.geometry_key()


# -- the schema and the round trip ------------------------------------------
def test_the_schema_accepts_the_field_and_rejects_a_negative():
    assert schema_errors(_doc([_roof(end_overhang_in=[24.0, 0.0])])) == []
    assert schema_errors(_doc([_roof(end_overhang_in=[-1.0, 0.0])])) != []
    assert schema_errors(_doc([_roof()])) == []               # absent is fine


def test_it_round_trips_and_a_zero_pair_writes_no_key(scene):
    doc = _doc([_roof("rf_rake", end_overhang_in=[24.0, 6.0]),
                _roof("rf_plain")])
    doc["roofs"][1]["ridge"] = [[0.0, 400.0], [200.0, 400.0]]
    apply_design_to_scene(scene, doc, report={})
    items = sorted((it for it in scene.items() if isinstance(it, RoofItem)),
                   key=lambda r: r.p1.y())
    assert items[0].end_overhang_in == [24.0, 6.0]
    assert items[1].end_overhang_in == [0.0, 0.0]
    out = design_from_scene(scene).to_dict()
    recs = sorted(out["roofs"], key=lambda r: r["ridge"][0][1])
    assert recs[0]["end_overhang_in"] == [24.0, 6.0]
    assert "end_overhang_in" not in recs[1], "a zero pair writes no key"
    assert schema_errors(out) == []
