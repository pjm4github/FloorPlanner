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

from floorplanner.config import DEFAULT_FLOOR, floor_elevations, set_floor_state
from floorplanner.items import DormerGripItem, DormerItem, make_furnishing
from floorplanner.parametric import dormer_geometry as dg
from floorplanner.parametric.dormers import DORMER
from floorplanner.parametric import findings as F
from floorplanner.parametric.findings import WARNING
from floorplanner.roofs import RoofItem
from floorplanner.rooms import RoomItem
from floorplanner.walls import OpeningItem, WallItem

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


def test_dragging_the_apex_slides_the_anchor_up_the_roof_clamped_at_the_ridge(scene):
    # P2-core-2 (2026-11-18): knob A is the ANCHOR -- it slides along the fall
    # line (the ridge rising with it) and may not cross the host ridge.
    _host(scene)                     # ridge along x at y=100 (uphill -y), ridge 132
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 160), new=True)
    d._recompute()
    r0, y0 = dg.ridge_height(d.params), d.pos().y()
    d.begin_knob()
    d.drag_knob("apex", QPointF(150, 120))       # pull up toward the ridge
    assert d.pos().y() < y0, "anchor slid up the roof"
    assert dg.ridge_height(d.params) > r0, "ridge rose with the anchor"
    d.drag_knob("apex", QPointF(150, 40))        # try to shove it over the ridge
    assert d.pos().y() >= 100.0 - 1e-6, "anchor stops at the host ridge"
    assert dg.ridge_height(d.params) <= 132.0 + 1e-6
    d.end_knob("apex", QPointF(150, 40))


def test_an_old_dormer_migrates_pos_from_face_to_anchor(scene):
    # P2 (2026-11-18): a record saved in the OLD frame (pos = face, no
    # 'anchored') moves pos UP the ridge to the anchor on the first rebuild in a
    # scene, keeping its shape -- the face stays where it was drawn.
    _host(scene)                     # ridge along x at y=100 (uphill is -y)
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150),
                state={"span_left_in": 60.0, "span_right_in": 60.0})
    assert d._migrate_anchor and not d.params.get("anchored")
    d._recompute()                               # settle -> migrate
    assert d.params["anchored"] and not d._migrate_anchor
    assert d.pos().y() < 150.0, "anchor moved uphill toward the host ridge"
    ux, uy = dg.ridge_direction(d.rotation())    # the face is pos shifted downhill
    face_y = d.pos().y() - uy * d._depth
    assert face_y == pytest.approx(150.0, abs=1.0), "the face stays where it was"


def test_param_context_exposes_the_host_eave_and_anchor(scene):
    # P1/P2 (2026-11-18): the host eave rides the context beside the ridge, and
    # the anchor's own host height (pos is the anchor) sits between them.
    _host(scene)                                   # eave 80, ridge 132
    d = _dormer(scene, pos=QPointF(150, 150), new=True)
    d._recompute()
    ctx = d.param_context()
    assert ctx.get("host_eave_in") == pytest.approx(80.0)
    za = ctx.get("host_anchor_in")                 # the host height at the anchor
    assert za is not None and 80.0 <= za <= 132.0
    ext = dg.host_extent(ctx["host_z_face_in"], ctx["host_slope"],
                         ctx["host_ridge_in"], ctx["host_eave_in"])
    assert ext is not None and ext["ridge_y"] > 0.0


def test_a_rotated_dormer_is_flagged_not_facing_downhill(scene):
    # P2 (2026-11-18): the host ridge runs along x, so the fall line is +/- y;
    # a rotation-0 dormer faces straight downhill, a turned one does not.
    _host(scene)
    _room(scene)
    d0 = _dormer(scene, pos=QPointF(150, 150), rotation=0.0, new=True)
    d0._recompute()
    assert d0.param_context().get("host_offaxis_deg") == pytest.approx(0.0, abs=0.5)
    assert d0._unbuildable is None
    d = _dormer(scene, pos=QPointF(150, 150), rotation=40.0, new=True)
    d._recompute()
    ctx = d.param_context()
    assert ctx.get("host_offaxis_deg") > dg.FACING_TOL_DEG
    _derived, findings = DORMER.evaluate(d.params, ctx)
    assert any(f.rule_id == "dormer.not_downhill" for f in findings)
    assert d._unbuildable == dg.NOT_DOWNHILL


def test_the_context_carries_the_wall_below_probe_and_a_face_type(scene):
    # P4b (2026-11-18): param_context runs the wall-below probe; with no floor
    # below there is none, and the face type is classified from the geometry.
    _host(scene)
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150), new=True)
    d._recompute()
    ctx = d.param_context()
    assert "wall_below" in ctx                        # the probe ran
    derived, _fs = DORMER.evaluate(d.params, ctx)
    assert derived["face_type"] in dg.FACE_TYPES


def test_over_no_roof_there_is_no_host_and_a_warning(scene):
    _room(scene)
    d = _dormer(scene, pos=QPointF(1000, 1000), new=True)   # far from any roof
    d._recompute()
    ctx = d.param_context()
    assert ctx.get("host_z_face_in") is None
    _derived, findings = DORMER.evaluate(d.params, ctx)
    assert any(f.rule_id == "dormer.no_host" for f in findings)


# -- 0359: born under the host ridge, and drawn red when over it -------------
def test_a_new_dormer_on_a_low_roof_is_born_under_the_ridge(scene):
    # The host ridge is 100 in; a default dormer would ride to 108, so the seed
    # must fit it under the ridge -- which only happens if items.py passes
    # host_ridge_in as the third arg to dg.default_state (0359).
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), eaves_h_in=60.0,
                  ridge_h_in=100.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    _room(scene, ceiling_in=96.0)
    d = _dormer(scene, pos=QPointF(150, 150), new=True)
    d._recompute()
    ctx = d.param_context()
    assert ctx.get("host_ridge_in") == pytest.approx(100.0)
    assert dg.ridge_height(d.params) <= 100.0 + 1e-6, "born over the host ridge"
    assert d._unbuildable is None


def test_an_anchored_dormer_ridge_equals_the_host_at_the_anchor(scene):
    # P2 (2026-11-18): on a roof the ridge IS the host height at the anchor
    # (pos). It is pinned there, under the host ridge; eaves/pitch float to hold
    # it -- so the over-ridge case is structurally prevented (the rule itself is
    # pinned in test_dormer_geometry).
    _host(scene)                     # eave 80, ridge 132
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150), new=True)
    d._recompute()
    za = d.param_context().get("host_anchor_in")
    assert za is not None
    assert dg.ridge_height(d.params) == pytest.approx(za, abs=0.5), "ridge = anchor"
    assert dg.ridge_height(d.params) <= 132.0 + 1e-6, "pinned under the host ridge"
    assert d._unbuildable is None


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


# -- the knobs A-G -----------------------------------------------------------
def test_selecting_a_dormer_shows_the_knobs_and_deselecting_hides_them(scene):
    d = _dormer(scene, new=True)
    assert d._grips == []
    d.setSelected(True)
    kinds = {g.kind for g in d._grips}
    assert kinds == set(DormerItem._GRIP_KINDS), kinds   # all 9 on a gable
    assert all(isinstance(g, DormerGripItem) for g in d._grips)
    d.setSelected(False)
    assert d._grips == []


def test_a_shed_has_both_side_knobs(scene):
    # the redesigned shed (2026-11-18) is a full box with two symmetric
    # trapezoid sides, so it carries the B/C/E knobs on BOTH sides, like a gable
    d = _dormer(scene, state={"form": "shed"})
    d.setSelected(True)
    kinds = {g.kind for g in d._grips}
    for k in ("span_l", "span_r", "guide_l", "guide_r", "eave_l", "eave_r"):
        assert k in kinds, k


def test_the_span_knob_resizes_and_symmetric_mirrors(scene):
    # default symmetric: dragging the left span knob sets BOTH halves
    d = _dormer(scene, pos=QPointF(150, 150))      # rotation 0
    d._recompute()
    d.begin_knob()
    # free=True: test the raw reshape math, not the grid snap (dg x = 80 is not
    # a 6" multiple; the snap is covered by its own test below)
    d.drag_knob("span_l", QPointF(230, 150), free=True)   # dg x = 80
    assert d.params["span_left_in"] == pytest.approx(80.0)
    assert d.params["span_right_in"] == pytest.approx(80.0), "symmetric mirror"
    d.end_knob("span_l", QPointF(230, 150), free=True)


def test_the_face_knob_sets_the_face_overhang(scene):
    d = _dormer(scene, pos=QPointF(150, 150))
    d._recompute()
    d.begin_knob()
    d.drag_knob("face", QPointF(150, 170), free=True)   # dg y = -20 -> overhang 20
    assert d.params["face_overhang_in"] == pytest.approx(20.0)
    d.end_knob("face", QPointF(150, 170), free=True)


def test_a_knob_snaps_its_dimension_to_the_grid_unless_shift(scene):
    """0360 (Patrick, 2026-11-22): a dormer control knob lands its dimension on
    the on-centre grid (`SETTINGS["wall_snap_in"]`, 6") by DEFAULT; holding Shift
    (`free=True`) drags free. dg x = 80 is not a 6" multiple, so it snaps to 78."""
    from floorplanner.config import SETTINGS
    from floorplanner.geometry import wall_snap_len
    d = _dormer(scene, pos=QPointF(150, 150))      # rotation 0, symmetric
    d._recompute()
    d.begin_knob()
    d.drag_knob("span_l", QPointF(230, 150))               # dg x = 80, default snaps
    step = SETTINGS["wall_snap_in"]
    snapped = d.params["span_left_in"]
    assert snapped == pytest.approx(wall_snap_len(80.0))   # 78 at the 6" grid
    assert round(snapped / step) * step == pytest.approx(snapped), "on the grid"
    assert snapped == d.params["span_right_in"], "symmetric mirror keeps up"
    d.drag_knob("span_l", QPointF(230, 150), free=True)    # Shift: exact, no snap
    assert d.params["span_left_in"] == pytest.approx(80.0)
    d.end_knob("span_l", QPointF(230, 150), free=True)


# -- knob D (the face wall, P3, purple) --------------------------------------
def test_knob_D_sets_the_face_distance_holding_the_eave(scene):
    # P3 (2026-11-18): knob D (purple) is the FACE WALL -- dragging it toward the
    # anchor shortens the face distance (depth) while the EAVE is held, so the
    # eave overhang grows by what the face gave up.
    d = _dormer(scene, pos=QPointF(150, 150))      # no host: migrates, face at 150
    d._recompute()
    d.setSelected(True)
    assert "guide_face" in {g.kind for g in d._grips}
    eave0 = d._depth + d.params["face_overhang_in"]
    d.begin_knob()
    d.drag_knob("guide_face", QPointF(150, 120))   # pull the face toward the anchor
    assert d.params["depth_in"] < 96.0, "face distance shortened"
    assert d._depth + d.params["face_overhang_in"] == pytest.approx(eave0), "eave held"
    d.end_knob("guide_face", QPointF(150, 120))


def test_a_shed_keeps_the_face_guide_knob(scene):
    d = _dormer(scene, state={"form": "shed"})
    d.setSelected(True)
    assert "guide_face" in {g.kind for g in d._grips}   # D is not a _r knob


# -- F1: the walls under the face and the sides, with their openings ---------
def _face_wall(scene, x0=100.0, x1=200.0, y=150.0, codes=()):
    """A wall square to a rotation-0 dormer's ridge, at its face (y=150)."""
    w = WallItem(QPointF(x0, y), QPointF(x1, y))
    w.floor = DEFAULT_FLOOR
    scene.addItem(w)
    for s, code in codes:
        op = OpeningItem(w, "window", code, s)
        w.openings.append(op)
    return w


def test_F1_gathers_the_face_wall_and_its_openings(scene):
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150),
                state={"span_left_in": 60.0, "span_right_in": 60.0})
    _face_wall(scene, codes=[(30.0, "3040"), (70.0, "3040")])
    d._recompute()                               # settle (migrate pos -> anchor)
    ctx = d.param_context()
    lo, hi = ctx["face_wall"]
    assert lo == pytest.approx(-50.0) and hi == pytest.approx(50.0)
    ops = ctx["face_openings"]
    assert len(ops) == 2
    assert all("x0" in o and "x1" in o and "sill_in" in o and "head_in" in o
               for o in ops)


def test_F1_face_is_bounded_to_the_dormer_width_not_a_neighbours_wall(scene):
    # Patrick, 2026-11-20 (`twoGableOneShed.json`): three dormers in a row, each
    # over its own window on the SAME collinear wall line. The left dormer's
    # face must gather ONLY the window under it -- not the neighbours' windows
    # further along the line ("I see the windows under the other 2 dormers").
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150),
                state={"span_left_in": 60.0, "span_right_in": 60.0})
    _face_wall(scene, x0=100.0, x1=200.0, codes=[(50.0, "3040")])   # under it, x=0
    # a neighbour's wall + window, collinear, well past the right side guide
    _face_wall(scene, x0=240.0, x1=340.0, codes=[(50.0, "3040")])   # x=+140
    d._recompute()
    ctx = d.param_context()
    ops = ctx["face_openings"]
    assert len(ops) == 1
    assert ops[0]["x0"] == pytest.approx(-15.0) and ops[0]["x1"] == pytest.approx(15.0)
    lo, hi = ctx["face_wall"]                       # clipped to the face width
    assert lo >= -60.0 - 1e-6 and hi <= 60.0 + 1e-6


def test_F1_reports_None_when_it_looked_and_found_no_face_wall(scene):
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150))      # a scene, but no wall drawn
    ctx = d.param_context()
    assert "face_wall" in ctx and ctx["face_wall"] is None     # looked, none
    # and the kind raises the ADVISORY for it
    _derived, findings = DORMER.evaluate(d.params, ctx)
    assert any(f.rule_id == "dormer.face_open" for f in findings)


def test_F1_is_absent_when_nobody_looked(scene):
    d = make_furnishing("dormer", QPointF(0, 0), new=True)     # not in a scene
    ctx = d.param_context()
    assert "face_wall" not in ctx       # absent != None: nobody looked


def test_F1_gathers_a_side_wall_on_a_side_guide(scene):
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150),
                state={"span_left_in": 60.0, "span_right_in": 60.0})
    # the left side guide is at dg x=+60 -> scene x=210; a wall there runs
    # along the ridge (dg +y is scene -y at rotation 0)
    w = WallItem(QPointF(210, 150), QPointF(210, 70))
    w.floor = DEFAULT_FLOOR
    scene.addItem(w)
    ctx = d.param_context()
    assert ctx["side_walls"]["left"] is not None
    assert ctx["side_walls"]["right"] is None


def test_F1_does_not_gather_while_a_knob_is_held(scene):
    # the gather must not run per-frame during a drag (0354 perf discipline)
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150))
    _face_wall(scene)
    d.begin_knob()                       # freezes the item
    ctx = d.param_context()
    assert "face_wall" not in ctx, "F1 ran during a held drag"
    d.end_knob("span_l", QPointF(150, 150))
    assert "face_wall" in d.param_context()      # and resumes after release


def test_the_knee_lines_are_held_during_a_knob_drag_and_settle_on_release(scene):
    # a tall dormer over no roof so its planes cross the 96in ceiling
    _room(scene, ceiling_in=96.0)
    state = dg.normalize_state({"eaves_h_in": 60.0, "span_left_in": 60.0,
                                "span_right_in": 60.0, "pitch_12": 10.0,
                                "depth_in": 96.0, "symmetric": True})
    d = _dormer(scene, pos=QPointF(150, 150), state=state)
    d._recompute()
    held = [tuple(seg) for seg in d._knees]
    assert held, "precondition: there are knee lines to hold"
    d.begin_knob()
    d.drag_knob("span_l", QPointF(150 + 40, 150))   # reshape (span 40)
    assert [tuple(seg) for seg in d._knees] == held, "knees must be HELD mid-drag"
    d.end_knob("span_l", QPointF(150 + 40, 150))
    # settled now: a valid (possibly changed) list, no crash
    assert isinstance(d._knees, list)


# -- the dialog preview: gable centred, side reads against the host roof (0360)-
def test_dialog_drops_the_symmetric_right_side_and_shows_the_host_roof(scene):
    # A symmetric dormer's right side is the left mirrored, so it is dropped:
    # the row reads [left side | gable end]. The side carries the HOST ROOF's
    # line (dashed, labelled) as its reference -- not a dormer-roof tent.
    _host(scene)
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150),
                state={"span_left_in": 60.0, "span_right_in": 60.0})
    ctx = d.param_context()
    derived, _findings = DORMER.evaluate(d.params, ctx)
    view = DORMER.make_preview(None)
    view.set_data(d.params, derived, ctx)
    row = view.panels()
    assert [t for t, _pn in row] == ["Left side", "Gable end"]
    left, gable = (pn for _t, pn in row)
    # the old dashed dormer-roof tent is gone from every panel
    assert "roof_ref" not in left and "roof_ref" not in gable
    # the gable carries no face mark and no host line; the side carries both
    assert gable["face_mark"] is False and gable["host"] is None
    assert left["face_mark"] is True and left["flip"] is True
    # the side's reference IS the host roof line: two points, a real rise
    assert isinstance(left["host"], list) and len(left["host"]) == 2


def test_dialog_keeps_the_right_side_when_the_dormer_is_asymmetric(scene):
    _host(scene)
    _room(scene)
    d = _dormer(scene, pos=QPointF(150, 150),
                state={"symmetric": False, "span_left_in": 72.0,
                       "span_right_in": 48.0})
    ctx = d.param_context()
    derived, _findings = DORMER.evaluate(d.params, ctx)
    view = DORMER.make_preview(None)
    view.set_data(d.params, derived, ctx)
    row = view.panels()
    assert [t for t, _pn in row] == ["Left side", "Gable end", "Right side"]
    left, _gable, right = (pn for _t, pn in row)
    # faces toward the centre: left cheek flipped, right cheek unflipped
    assert left["flip"] is True and right["flip"] is False
    assert right["face_mark"] is True


# -- P5: the room/wall below the dormer, and the "nothing below" warning -----
def _with_floor_below():
    """Register a storey 'L0' below DEFAULT_FLOOR; returns a restore callable
    (the floor cache is a module global, so each test must put it back)."""
    prior = floor_elevations()
    set_floor_state(elevations={DEFAULT_FLOOR: 120.0, "L0": 0.0})
    return lambda: set_floor_state(elevations=prior)


def _room_on(scene, floor, rect=(-300.0, -300.0, 900.0, 900.0)):
    from PyQt6.QtGui import QPainterPath
    path = QPainterPath()
    path.addRect(*rect)
    room = RoomItem("Below", QPointF(150, 150), path, 100.0)
    room.floor = floor
    scene.addItem(room)
    return room


def test_room_below_probe_sees_a_room_on_the_floor_below(scene):
    restore = _with_floor_below()
    try:
        _host(scene)
        d = _dormer(scene, pos=QPointF(150, 150), new=True)
        d._recompute()
        assert d.param_context().get("room_below") is False   # looked, none yet
        _room_on(scene, "L0")
        assert d.param_context().get("room_below") is True
    finally:
        restore()


def test_room_below_is_none_with_no_lower_floor(scene):
    _host(scene)
    d = _dormer(scene, pos=QPointF(150, 150), new=True)
    d._recompute()
    assert d.param_context().get("room_below") is None   # DEFAULT_FLOOR is lowest


def test_nothing_below_warns_when_the_storey_is_undefined(scene):
    # P5 (Patrick, 2026-11-19): a prominent WARNING when neither room nor wall
    # is defined below a non-cantilever dormer; it clears once a room is drawn.
    restore = _with_floor_below()
    try:
        _host(scene)
        # anchor near the ridge with a modest depth so the face sits ON the
        # host roof (a setback), not past the eave (a cantilever, which is the
        # one face that rightly has nothing below it).
        d = _dormer(scene, pos=QPointF(150, 115), state={"depth_in": 20.0},
                    new=True)
        d._recompute()
        derived, findings = DORMER.evaluate(d.params, d.param_context())
        assert derived["face_type"] != dg.FACE_CANTILEVER
        assert any(f.rule_id == "dormer.nothing_below" and f.severity == WARNING
                   for f in findings)
        _room_on(scene, "L0")
        _d2, cleared = DORMER.evaluate(d.params, d.param_context())
        assert not any(f.rule_id == "dormer.nothing_below" for f in cleared)
    finally:
        restore()


def test_the_dormer_pitch_field_offers_degrees_or_rise_run(scene):
    # Patrick (2026-11-19): a per-field unit dropdown, degrees or rise/run,
    # the choice remembered. The stored pitch_12 never changes on a unit flip.
    import math as _m
    from floorplanner import config
    from floorplanner.parametric.dialog import ParametricDialog
    config.set_pitch_units("")                        # unset -> the dormer's native in 12
    d = _dormer(scene, pos=QPointF(150, 150))
    dlg = ParametricDialog(DORMER, d.draft_state(), d.param_context())
    try:
        combo = dlg._unit_combos.get("pitch_12")
        spin = dlg._widgets["pitch_12"]
        assert combo is not None
        assert {combo.itemData(i) for i in range(combo.count())} == {"in12", "deg"}
        assert dlg._unit_mode["pitch_12"].key == "in12"      # native
        canonical = float(dlg.values["pitch_12"])
        combo.setCurrentIndex(combo.findData("deg"))
        assert spin.suffix().strip() == "deg"
        assert dlg.values["pitch_12"] == pytest.approx(canonical, abs=1e-6)
        assert spin.value() == pytest.approx(
            _m.degrees(_m.atan2(canonical, 12.0)), abs=0.05)
        assert config.pitch_units() == "deg"             # remembered
        combo.setCurrentIndex(combo.findData("in12"))    # flip back, no drift
        assert dlg.values["pitch_12"] == pytest.approx(canonical, abs=1e-6)
    finally:
        dlg.deleteLater()


def test_typing_a_unit_in_the_dormer_pitch_sets_degrees_or_rise_run(scene):
    # Patrick (2026-11-19): "d"/"deg" after the number -> degrees, else rise/run.
    import math as _m
    from PyQt6.QtWidgets import QApplication
    from floorplanner import config
    from floorplanner.parametric.dialog import ParametricDialog
    config.set_pitch_units("")
    d = _dormer(scene, pos=QPointF(150, 150))
    dlg = ParametricDialog(DORMER, d.draft_state(), d.param_context())
    try:
        spin = dlg._widgets["pitch_12"]
        assert dlg._unit_mode["pitch_12"].key == "in12"           # native
        spin.lineEdit().setText("40 deg")
        spin.interpretText()
        QApplication.processEvents()                              # deferred unitTyped
        assert dlg._unit_mode["pitch_12"].key == "deg"
        assert spin.value() == pytest.approx(40.0, abs=0.02)
        assert dlg.values["pitch_12"] == pytest.approx(
            12.0 * _m.tan(_m.radians(40.0)), abs=0.02)
        assert config.pitch_units() == "deg"
        spin.lineEdit().setText("8")                              # bare -> rise/run
        spin.interpretText()
        QApplication.processEvents()
        assert dlg._unit_mode["pitch_12"].key == "in12"
        assert dlg.values["pitch_12"] == pytest.approx(8.0, abs=0.02)
    finally:
        dlg.deleteLater()


def test_a_too_steep_shed_can_be_accepted_to_fix_on_the_plan(scene):
    # Patrick (2026-11-19): switching to a shed can leave it too steep for the
    # host (the shed's back never dies in). That ERROR must not TRAP the user --
    # it is overridable, so OK (with the ack) keeps the red dormer on the plan to
    # fix there. A pure input error (zero pitch) still hard-blocks.
    from floorplanner.parametric.dialog import ParametricDialog
    _host(scene)                                   # host slope ~6.24 in 12
    d = _dormer(scene, pos=QPointF(150, 115),
                state={"form": "shed", "depth_in": 20.0}, new=True)
    d._recompute()
    dlg = ParametricDialog(DORMER, d.draft_state(), d.param_context())
    try:
        assert "dormer.too_steep" in [f.rule_id for f in dlg.findings()]
        assert not dlg.try_accept()                # the override needs the ack
        dlg.ack.setChecked(True)
        assert dlg.try_accept()                    # overridable -> accepted
        # a pure input error (zero pitch) is a HARD block -- not an override,
        # not a suggestive check -- so it blocks regardless of the ack. The
        # pitch spinbox clamps 0 back to its minimum on a widget read, so the
        # zero lands at the findings level; that a hard block stops OK is
        # proven directly in test_stair_item (tread 9.5, which the spinbox keeps).
        dlg.set_value("pitch_12", 0.0)
        assert F.blocks(dlg.findings())            # dormer.flat, non-overridable
    finally:
        dlg.deleteLater()


def test_the_knob_tooltips_name_the_face_wall_knee_wall_and_dormer_eave(scene):
    # Patrick (2026-11-19): hover tooltips explaining the knobs.
    tips = DormerGripItem._TIPS
    assert "face wall" in tips["guide_face"].lower()
    assert "knee wall" in tips["guide_l"].lower() and "knee wall" in tips["guide_r"].lower()
    assert "dormer eave" in tips["eave_l"].lower() and "dormer eave" in tips["eave_r"].lower()


def test_number_fields_recalc_on_focus_out_not_each_keystroke(scene):
    # a spinbox must not recalc mid-typing: a half-entered number would feed
    # the ridge/eaves/pitch coupling partial values and lock a field out of
    # range (Patrick, 2026-11-18). Keyboard tracking off => it signals on
    # focus-out / Enter / arrow-step, not on every keystroke.
    from floorplanner.parametric.dialog import ParametricDialog
    d = _dormer(scene, pos=QPointF(150, 150))
    dlg = ParametricDialog(DORMER, d.draft_state(), d.param_context())
    try:
        for key in ("ridge_h_in", "eaves_h_in", "pitch_12", "span_left_in"):
            assert dlg._widgets[key].keyboardTracking() is False
    finally:
        dlg.deleteLater()
