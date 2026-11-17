"""0352 phase 2 -- the DORMER furnishing item.

A dormer is a furnishing now: placed from the palette, it OWNS NO WALL and
draws only its own roof lines, the control guides and the KNEE LINES where its
planes cross the room ceiling. These check the item's wiring -- it is built by
`make_furnishing`, it keeps no wall, its parameters round-trip through a
document, and it finds its host roof by height (knee lines appear over a roof
and the "no host" finding is raised over none). The pure arithmetic is
`tests/test_dormer_geometry.py`; this is the Qt item on top of it.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.items import DormerItem, make_furnishing
from floorplanner.parametric import dormer_geometry as dg
from floorplanner.parametric.dormers import DORMER
from floorplanner.roofs import RoofItem
from floorplanner.rooms import RoomItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.rooms

# A host roof: ridge along x at y=100, falling to both sides (slope 0.52).
EAVES_H, RIDGE_H, SPAN = 80.0, 132.0, 100.0


def _host(scene):
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), eaves_h_in=EAVES_H,
                  ridge_h_in=RIDGE_H, span_in=SPAN)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _room(scene, ceiling_in=96.0):
    from PyQt6.QtGui import QPainterPath
    path = QPainterPath()
    path.addRect(0, 0, 300, 200)
    room = RoomItem("Room", QPointF(150, 100), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _dormer(scene, pos=None, rotation=0.0, state=None, new=False):
    it = make_furnishing("dormer", pos or QPointF(150, 150), rotation,
                         state or {}, new=new)
    it.floor = DEFAULT_FLOOR
    scene.addItem(it)
    return it


# -- make_furnishing builds the right item ------------------------------------
def test_make_furnishing_builds_a_dormer_item():
    it = make_furnishing("dormer", QPointF(10, 10), new=True)
    assert isinstance(it, DormerItem)
    assert it.is_parametric()                       # registered kind
    assert it.kind == "dormer"
    # the state is a complete, normalized dormer state
    assert set(it.extra_state()) == set(dg.STATE_DEFAULTS)


# -- it owns no wall ----------------------------------------------------------
def test_a_dormer_mints_no_wall(scene):
    _host(scene)
    _room(scene)
    before = [w for w in scene.items() if isinstance(w, WallItem)]
    d = _dormer(scene, new=True)
    d._recompute()
    after = [w for w in scene.items() if isinstance(w, WallItem)]
    assert after == before == [], "a dormer furnishing draws no wall"


# -- the state round-trips through a document ---------------------------------
def test_state_round_trips_through_a_document():
    from floorplanner.mainwindow import MainWindow
    win = MainWindow()
    state = dg.normalize_state({"form": "gable", "span_left_in": 72.0,
                                "span_right_in": 48.0, "symmetric": False,
                                "eaves_h_in": 54.0, "pitch_12": 8.0})
    d = make_furnishing("dormer", QPointF(200, 200), 90.0, state)
    d.floor = DEFAULT_FLOOR
    win.scene.addItem(d)
    doc = win.design_document()
    recs = [f for f in doc.get("furnishings", []) if f["kind"] == "dormer"]
    assert len(recs) == 1, doc.get("furnishings")
    saved = recs[0]["state"]
    for k, v in dg.STATE_DEFAULTS.items():
        if isinstance(v, float):
            assert abs(float(saved[k]) - float(state[k])) < 1e-6, k
        else:
            assert saved[k] == state[k], k
    # reopen and the dormer comes back as a DormerItem with the same state
    win2 = MainWindow()
    win2.open_document(doc, interactive=False)
    got = [it for it in win2.scene.items() if isinstance(it, DormerItem)]
    assert len(got) == 1
    assert got[0].extra_state() == d.extra_state()


# -- the host is found by height --------------------------------------------
def test_finds_its_host_over_a_roof(scene):
    _host(scene)
    _room(scene, ceiling_in=96.0)
    d = _dormer(scene, pos=QPointF(150, 150), rotation=0.0, new=True)
    d._recompute()
    ctx = d.param_context()
    assert ctx.get("host_z_face_in") is not None, "no host found over the roof"
    assert ctx["host_slope"] > 0.0


def test_over_no_roof_there_is_no_host_and_a_warning(scene):
    _room(scene)
    d = _dormer(scene, pos=QPointF(1000, 1000), new=True)   # far from any roof
    d._recompute()
    ctx = d.param_context()
    assert ctx.get("host_z_face_in") is None
    _derived, findings = DORMER.evaluate(d.params, ctx)
    assert any(f.rule_id == "dormer.no_host" for f in findings)


# -- knee lines where the planes cross the room ceiling ----------------------
def test_draws_knee_lines_where_the_planes_cross_the_ceiling(scene):
    # a tall dormer over NO roof (ridge well above the 96in ceiling): each
    # plane crosses the ceiling, so both sides get a knee line drawn full depth
    _room(scene, ceiling_in=96.0)
    state = dg.normalize_state({"eaves_h_in": 60.0, "span_left_in": 60.0,
                                "span_right_in": 60.0, "pitch_12": 10.0,
                                "depth_in": 96.0})
    d = _dormer(scene, pos=QPointF(150, 150), state=state)
    d._recompute()
    assert dg.ridge_height(d.params) > 96.0
    assert len(d._geo["knees"]) == 2, d._geo["knees"]


# -- the item's extent stays finite and covers its own lines ------------------
def test_bounding_rect_is_finite_and_nonempty(scene):
    _host(scene)
    _room(scene)
    d = _dormer(scene, new=True)
    d._recompute()
    r = d.boundingRect()
    assert r.isValid() and r.width() > 0 and r.height() > 0
    assert all(abs(v) < 1e5 for v in (r.left(), r.right(), r.top(), r.bottom()))
