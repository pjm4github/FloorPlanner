"""R6.b (0197-ruling.md sec5; 0186-ruling.md sec4): THE BUILDING HAS ONE
ROOFSCAPE. Composition runs in ABSOLUTE height -- a roof's surface is its
level's `elevation_in` plus its own heights -- over every live roof of
the building, not per level. "The same rules, one more term in z; no new
geometry class": `compute_roof_clips` is untouched and is handed
`roofclip.Lifted` views; `compose_building` is the entry point;
`roofs.sync_roof_clips` and `fp3d.build_model` both compose the building.

The receipts are INVARIANCES, because they cannot be satisfied by
accident: a common elevation changes nothing; lifting a roof to another
level while lowering its heights by that level's elevation changes
nothing; and the converse -- the same heights a storey up -- changes
exactly the ground the lifted roof now stands over.

The miniature is tests/test_roof_intersection.py's L: a main ridge along
x at y=200 (eaves 96 / ridge 150, span 100) and a wing ridge along y at
x=200 from y=150 to y=500 (eaves 96 / ridge 130, span 60).
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.config import DEFAULT_FLOOR, floor_elevations, set_floor_state
from floorplanner.roofclip import (
    Lifted, Pt, RoofGeom, _area, _contains, compose_building,
    compute_roof_clips, footprint_polygon, surface_height,
)
from floorplanner.roofs import RoofItem, hold_roof_clips, sync_roof_clips

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "wiscaway-2level-stacked-floor.json"


def _geom(ridge, eaves, ridge_h, span, rid):
    return RoofGeom.from_record({"id": rid, "ridge": ridge, "eaves_h_in": eaves,
                                 "ridge_h_in": ridge_h, "overhang_in": [0, 0],
                                 "span_in": [span, span]})


def _main():
    return _geom([[0, 200], [400, 200]], 96.0, 150.0, 100.0, "main")


def _wing(drop=0.0):
    return _geom([[200, 150], [200, 500]], 96.0 - drop, 130.0 - drop, 60.0, "wing")


def _facts(clip):
    area = None if clip.region is None else round(clip.region.area(), 6)
    seams = sorted({(round(p.x(), 6), round(p.y(), 6)) for s in clip.seams for p in s})
    return area, seams


# --------------------------------------------------------------------------
# the lifted view
# --------------------------------------------------------------------------
def test_lifted_raises_the_two_heights_and_nothing_else():
    g = _main()
    lf = Lifted(g, 100.0)
    assert lf.roof is g
    assert (lf.ridge_h_in, lf.eaves_h_in) == (250.0, 196.0)
    assert lf.span_in == g.span_in and lf.gable == g.gable and lf.p1 is g.p1
    assert [(p.x(), p.y()) for p in footprint_polygon(lf)] == \
        [(p.x(), p.y()) for p in footprint_polygon(g)]
    for pt in (Pt(100, 200), Pt(100, 250), Pt(399, 101)):
        assert surface_height(lf, pt) == pytest.approx(surface_height(g, pt) + 100.0)


# --------------------------------------------------------------------------
# the invariances
# --------------------------------------------------------------------------
def test_a_common_elevation_changes_nothing():
    m, w = _main(), _wing()
    one = compute_roof_clips([m, w])
    both = compose_building([(m, 37.0), (w, 37.0)])
    for rf in (m, w):
        assert _facts(both[id(rf)]) == _facts(one[id(rf)])
        assert both[id(rf)].ext == one[id(rf)].ext


def test_lifting_a_roof_and_lowering_its_heights_by_the_same_amount_changes_nothing():
    m, w = _main(), _wing()
    one = compute_roof_clips([m, w])
    low = _wing(drop=100.0)                      # heights 100 lower...
    lifted = compose_building([(m, 0.0), (low, 100.0)])      # ...a storey up
    assert _facts(lifted[id(m)]) == _facts(one[id(m)])
    assert _facts(lifted[id(low)]) == _facts(one[id(w)])
    assert _facts(one[id(m)]) == (76222.222222, [(140.0, 300.0), (200.0, 237.037037),
                                                 (260.0, 300.0)])


def test_the_same_heights_a_storey_up_take_exactly_the_ground_stood_over():
    """The wing 100in higher stands wholly above the main (its eaves at
    196 over the main's 150 ridge): it owns everything under it and no
    seam is left. The main loses exactly the overlap, 120 x 200 -- which
    includes the wing's JOINED EXTENSION past its own end to the main's
    far eave: the crossed-arm rule (0184) reads the plan, not the
    height, so an upper roof whose end has crossed a lower roof's ridge
    still takes its extension over it. Pinned here and named in
    0200-report.md; his own fixture has no such arm."""
    m, w = _main(), _wing()
    per = compose_building([(m, 0.0), (w, 100.0)])
    assert _facts(per[id(m)]) == (56000.0, [])
    assert _facts(per[id(w)]) == (48000.0, [])
    assert per[id(w)].region.contains(Pt(200, 200)), "the main's ridge, under the wing"
    assert not per[id(m)].region.contains(Pt(200, 200))
    assert per[id(m)].region.contains(Pt(50, 200))


# --------------------------------------------------------------------------
# the editor: one roofscape, elevations from the floor state
# --------------------------------------------------------------------------
def _items(scene, wing_floor="Second"):
    m = RoofItem(QPointF(0, 200), QPointF(400, 200), span_in=100.0, overhang_in=0.0,
                 ridge_h_in=150.0, eaves_h_in=96.0)
    m.floor = DEFAULT_FLOOR
    scene.addItem(m)
    w = RoofItem(QPointF(200, 150), QPointF(200, 500), span_in=60.0, overhang_in=0.0,
                 ridge_h_in=130.0, eaves_h_in=96.0)
    w.floor = wing_floor
    scene.addItem(w)
    sync_roof_clips(scene)
    return m, w


def test_roofs_on_different_floors_compose_at_their_elevations(scene):
    m, w = _items(scene)
    # no elevation known (a bare scene): one datum, the single-level answer
    assert m._clip_region.area() == pytest.approx(76222.222222)
    assert w._clip_region.area() == pytest.approx(27777.777778)
    set_floor_state(elevations={DEFAULT_FLOOR: 0.0, "Second": 100.0})
    sync_roof_clips(scene)
    assert m._clip_region.area() == pytest.approx(56000.0)
    assert w._clip_region.area() == pytest.approx(48000.0)
    assert m.seams() == [] and w.seams() == []


def test_the_floor_argument_no_longer_scopes_the_composition(scene):
    m, w = _items(scene)
    set_floor_state(elevations={"Second": 100.0})
    sync_roof_clips(scene, DEFAULT_FLOOR)          # every caller names a floor
    assert w._clip_region.area() == pytest.approx(48000.0)


def test_changing_a_floors_elevation_recomposes_the_building(fp, win):
    win.prepare_headless()
    win.new_floor_named("Second")                  # elevation 96 by default
    win.set_floor_levels("Second", 0.0, 96.0)
    m, w = _items(win.scene)
    assert floor_elevations() == {fp.DEFAULT_FLOOR: 0.0, "Second": 0.0}
    assert w._clip_region.area() == pytest.approx(27777.777778)
    win.set_floor_levels("Second", 100.0, 96.0)
    assert floor_elevations()["Second"] == 100.0
    assert w._clip_region.area() == pytest.approx(48000.0), \
        "the elevation edit must re-compose, not wait for the next roof edit"


def test_a_held_scene_composes_once_at_the_release(scene):
    m, w = _items(scene)
    before = w._clip_region.area()
    hold_roof_clips(scene, True)
    w.set_ridge(QPointF(200, 150), QPointF(200, 400))      # rebuild -> sync, held
    assert w._clip_region.area() == pytest.approx(before), "held: nothing recomposed"
    hold_roof_clips(scene, False)
    assert w._clip_region.area() != pytest.approx(before), "released: composed"


# --------------------------------------------------------------------------
# his fixture
# --------------------------------------------------------------------------
def test_his_fixture_composes_with_no_blank_and_no_double_ownership():
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    elev = {L["id"]: float(L["elevation_in"]) for L in doc["levels"]}
    assert elev == {"L1": 0.0, "L2": 100.0}
    geoms = [(r["id"], RoofGeom.from_record(r), elev[r["level"]]) for r in doc["roofs"]]
    diag = {}
    per = compose_building([(g, dz) for _, g, dz in geoms], diag=diag)
    assert diag["blank"] == [], "ground under the roofscape drawn by nobody"
    regions = {rid: per[id(g)].region for rid, g, _ in geoms}
    assert all(r is not None for r in regions.values())
    areas = {rid: round(r.area()) for rid, r in regions.items()}
    assert areas == {"rf1": 96292, "rf2": 177732, "rf3": 233861, "rf4": 36043,
                     "rf5": 19903, "rf6": 35958}
    fps = {rid: footprint_polygon(g) for rid, g, _ in geoms}
    # rf1, L1's main roof, is what the upper roofs stand over: per level it
    # kept 91% of its footprint (0200-report.md sec2); composed, under a quarter
    assert areas["rf1"] / _area(fps["rf1"]) < 0.25
    xs = [p.x() for fp in fps.values() for p in fp]
    ys = [p.y() for fp in fps.values() for p in fp]
    seen = twice = nobody = 0
    x = min(xs) + 3.7
    while x < max(xs):
        y = min(ys) + 4.3
        while y < max(ys):
            pt = Pt(x, y)
            if any(_contains(fp, pt) for fp in fps.values()):
                seen += 1
                owners = sum(1 for r in regions.values() if r.contains(pt))
                twice += owners > 1
                nobody += owners == 0
            y += 24.0
        x += 24.0
    assert seen > 1000 and twice == 0 and nobody == 0


def test_the_app_loads_his_fixture_composed_as_a_building(fp, win):
    win.prepare_headless()
    win.load_path(str(FIXTURE))
    assert floor_elevations() == {"default": 0.0, "upper": 100.0}
    main = next(it for it in win.scene.items()
                if isinstance(it, RoofItem) and it.floor == "default"
                and round(it.p1.x()) == 150)
    assert main._clip_region.area() == pytest.approx(96292.1, abs=0.5)


# --------------------------------------------------------------------------
# 3D: one roofscape, walls capped across levels, no climb across levels
# --------------------------------------------------------------------------
def _load_fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_r6b_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


LEVELS = [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0},
          {"id": "L2", "elevation_in": 100.0, "height_in": 96.0}]


def _rec(rid, level, ridge, eaves, ridge_h, span, **kw):
    return {"id": rid, "level": level, "ridge": ridge, "eaves_h_in": eaves,
            "ridge_h_in": ridge_h, "overhang_in": [0, 0], "span_in": [span, span], **kw}


def _roof_mesh(fp3d, roofs):
    doc = {"levels": LEVELS, "vertices": [], "walls": [], "rooms": [],
           "furnishings": [], "roofs": roofs}
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    assert not model.notes, model.notes
    return next(m for m in model.meshes if m.name == "roofs")


def test_the_3d_roofscape_is_invariant_under_lift_and_lower():
    fp3d = _load_fp3d()
    one = _roof_mesh(fp3d, [_rec("m", "L1", [[0, 200], [400, 200]], 96.0, 150.0, 100.0),
                            _rec("w", "L1", [[200, 150], [200, 500]], 96.0, 130.0, 60.0)])
    two = _roof_mesh(fp3d, [_rec("m", "L1", [[0, 200], [400, 200]], 96.0, 150.0, 100.0),
                            _rec("w", "L2", [[200, 150], [200, 500]], -4.0, 30.0, 60.0)])
    assert one.verts.shape == two.verts.shape
    assert np.allclose(one.verts, two.verts, atol=1e-9)
    assert np.array_equal(one.faces, two.faces)


def _wall_verts(model):
    return np.vstack([m.verts for m in model.meshes if m.name.startswith("walls:")])


def test_a_wall_on_the_upper_level_is_capped_by_a_lower_levels_roof_rising_through_it():
    """L1's roof (eaves 96 / ridge 296, span 200: slope 1) rises through
    L2 (base 100, walls to 196). An L2 wall 150in off the ridge stands
    where that roof is 146in -- its near face 147.75 off, so its highest
    point is 296 - 147.75 - 4.5 = 143.75, not its own 196."""
    fp3d = _load_fp3d()
    doc = {"levels": LEVELS,
           "vertices": [{"id": "a", "x": 100, "y": 50}, {"id": "b", "x": 300, "y": 50}],
           "walls": [{"id": "w1", "level": "L2", "v1": "a", "v2": "b", "type": "interior"}],
           "rooms": [], "furnishings": [],
           "roofs": [_rec("rf1", "L1", [[0, 200], [400, 200]], 96.0, 296.0, 200.0)]}
    v = _wall_verts(fp3d.build_model(doc, furnishings=False, floors=False))
    assert v[:, 2].min() == pytest.approx(100.0)
    assert v[:, 2].max() == pytest.approx(143.75)
    # the control: without the roof the wall stands its full storey
    v0 = _wall_verts(fp3d.build_model(doc, furnishings=False, floors=False, roofs=False))
    assert v0[:, 2].max() == pytest.approx(196.0)


def test_a_wall_does_not_climb_into_a_dormer_a_storey_above():
    fp3d = _load_fp3d()
    host = _rec("h", "L2", [[0, 100], [400, 100]], 96.0, 150.0, 100.0)
    host["overhang_in"] = [12, 12]
    dormer = _rec("d", "L2", [[200, 190], [200, 125.926]], 116.0, 136.0, 30.0,
                  marker_end=0, host="h")
    doc = {"levels": LEVELS,
           "vertices": [{"id": "a", "x": 100, "y": 170}, {"id": "b", "x": 300, "y": 170}],
           "walls": [{"id": "w1", "level": "L1", "v1": "a", "v2": "b", "type": "interior"},
                     {"id": "w2", "level": "L2", "v1": "a", "v2": "b", "type": "interior"}],
           "rooms": [], "furnishings": [], "roofs": [host, dormer]}
    v = _wall_verts(fp3d.build_model(doc, furnishings=False, floors=False))
    lower = v[v[:, 2] <= 96.0 + 1e-6]
    upper = v[v[:, 2] >= 100.0 - 1e-6]
    assert len(lower) + len(upper) == len(v), "nothing between the two storeys"
    assert lower[:, 2].max() == pytest.approx(96.0), "L1's wall stops at its own top"
    assert upper[:, 2].max() == pytest.approx(100.0 + 136.0 - fp3d.WALL_CAP_BELOW_ROOF_IN), \
        "L2's wall climbs into its own level's dormer"
