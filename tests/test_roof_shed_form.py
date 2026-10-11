"""0248-report.md sec3, plans A and C, on Patrick's word ("Implement plan A
and C from 0248").

PLAN A -- the `shed` roof form: one plane off the ridge, down the LEFT
side only (`span_in[0]`); the right span and overhang are 0, legal in the
schema only on a shed. The record, the dataclass, the writer and reader,
the item (its setters clamp), the End-On dialog (a Form row; a shed's
right side locked at 0), the clip's record twin and the 3D builder (no
degenerate plane; a shed dormer's two ends are both faces).

PLAN C -- a dormer's generated side or face yields to a house wall
standing on its line: the wall beneath climbs into the dormer with its
own openings, and a generated piece on the same line buried them (his
house model, 0248 sec2 items 2 and 3).
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.validate import schema_errors
from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_shed_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(roofs, walls=(), vertices=(), levels=None):
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": levels or [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                                   "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": list(vertices), "walls": list(walls), "rooms": [], "furnishings": [],
            "groups": [], "roofs": list(roofs)}


def _roof(rid="rf1", form=None, span=(100.0, 100.0), **kw):
    r = {"id": rid, "level": "L1", "ridge": [[0.0, 100.0], [200.0, 100.0]], "eaves_h_in": 96.0,
         "ridge_h_in": 132.0, "overhang_in": [0.0, 0.0], "span_in": list(span),
         "eaves_bind": "manual", "gable": [True, True], "marker_end": 1}
    if form is not None:
        r["form"] = form
    r.update(kw)
    return r


# ---------------------------------------------------------------------------
# plan A: the record
# ---------------------------------------------------------------------------
def test_a_zero_right_span_is_legal_on_a_shed_and_on_nothing_else():
    assert schema_errors(_doc([_roof(form="shed", span=(100.0, 0.0))])) == []
    assert schema_errors(_doc([_roof(form="gable", span=(100.0, 0.0))])) != []
    assert schema_errors(_doc([_roof(span=(100.0, 0.0))])) != []          # no form = gable
    assert schema_errors(_doc([_roof(form="shed", span=(0.0, 100.0))])) != []   # the LEFT side must exist
    assert schema_errors(_doc([_roof(form="hip")])) != []                 # not a form (yet)
    assert schema_errors(_doc([_roof()])) == []                            # today's roofs unchanged


def test_the_item_holds_a_sheds_right_side_at_zero_whatever_it_is_handed():
    rf = RoofItem(QPointF(0, 100), QPointF(200, 100), span_in=[100.0, 100.0],
                  overhang_in=[12.0, 12.0], form="shed")
    assert rf.form == "shed"
    assert rf.span_in == [100.0, 0.0] and rf.overhang_in == [12.0, 0.0]
    rf.span_in = [120.0, 50.0]
    rf.overhang_in = 6.0
    assert rf.span_in == [120.0, 0.0] and rf.overhang_in == [6.0, 0.0]
    # the eave ends collapse onto the ridge on the right: a one-plane footprint
    e1a, e1b, e2a, e2b = rf._eave_ends()
    assert (e2a.x(), e2a.y()) == (0.0, 100.0) and (e2b.x(), e2b.y()) == (200.0, 100.0)
    assert e1a.y() == pytest.approx(100.0 + 126.0)                 # left: span + overhang
    # the right eave grip does nothing on a shed; the left one still drags
    rf.drag_eave(1, QPointF(100, 40))
    assert rf.span_in == [120.0, 0.0]
    rf.drag_eave(0, QPointF(100, 100 + 150))          # the grip lands on the 6in grid: 252
    assert rf.span_in[0] == pytest.approx(152.0 - 6.0)
    # back to a gable: the right side takes the left span
    rf.set_form("gable")
    assert rf.form == "gable" and rf.span_in == [146.0, 146.0]
    # a bad form is a gable
    assert RoofItem(QPointF(0, 0), QPointF(10, 0), form="dome").form == "gable"


def test_the_form_round_trips_through_the_document_and_a_gable_writes_none(scene):
    doc = _doc([_roof("rf_shed", form="shed", span=(100.0, 0.0), overhang_in=[12.0, 0.0]),
                _roof("rf_gab", span=(80.0, 90.0))])
    doc["roofs"][1]["ridge"] = [[0.0, 400.0], [200.0, 400.0]]
    rep = {}
    apply_design_to_scene(scene, doc, report=rep)
    items = sorted((it for it in scene.items() if isinstance(it, RoofItem)), key=lambda r: r.p1.y())
    assert [it.form for it in items] == ["shed", "gable"]
    assert items[0].span_in == [100.0, 0.0]
    out = design_from_scene(scene).to_dict()
    recs = sorted(out["roofs"], key=lambda r: r["ridge"][0][1])
    assert recs[0]["form"] == "shed" and recs[0]["span_in"] == [100.0, 0.0]
    assert "form" not in recs[1], "a gable writes no form key: older readers see what they always saw"
    assert schema_errors(out) == []


def test_the_end_on_dialog_locks_a_sheds_right_side_and_writes_the_form(scene):
    from floorplanner.dialogs import RoofEndOnDialog
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), span_in=[100.0, 0.0], form="shed")
    scene.addItem(rf)
    dlg = RoofEndOnDialog(rf)
    assert dlg.cb_form.currentIndex() == 1 and dlg.form_value() == "shed"
    assert dlg.sp_span_r.value() == 0.0 and not dlg.sp_span_r.isEnabled()
    assert not dlg.sp_oh_r.isEnabled() and not dlg.ck_oh_same.isEnabled()
    # to a gable: the right side opens and takes the left span
    dlg.cb_form.setCurrentIndex(0)
    assert dlg.sp_span_r.isEnabled() and dlg.sp_span_r.value() == pytest.approx(100.0)
    assert dlg.apply() and rf.form == "gable" and rf.span_in == [100.0, 100.0]
    # and back: the form is written before the spans, so the setter clamps
    dlg2 = RoofEndOnDialog(rf)
    assert dlg2.form_value() == "gable"
    dlg2.cb_form.setCurrentIndex(1)
    assert dlg2.sp_span_r.value() == 0.0
    assert dlg2.apply() and rf.form == "shed" and rf.span_in == [100.0, 0.0]
    out = design_from_scene(scene).to_dict()
    assert out["roofs"][0]["form"] == "shed" and schema_errors(out) == []


# ---------------------------------------------------------------------------
# plan A: the clip's twin and the 3D builder
# ---------------------------------------------------------------------------
def test_the_clip_twin_reads_the_form_and_a_shed_is_one_plane(fp3d):
    RC = fp3d.ROOFCLIP
    g = RC.RoofGeom.from_record(_roof(form="shed", span=(100.0, 40.0), overhang_in=[12.0, 9.0]))
    assert g.form == "shed" and g.span_in == [100.0, 0.0] and g.overhang_in == [12.0, 0.0]
    fp = RC.footprint_polygon(g)
    ys = sorted({round(p.y(), 3) for p in fp})
    assert ys == [100.0, 212.0], ys                 # the ridge edge and the eave, nothing beyond
    # the surface: at the ridge 132, down the left side, flat (ridge height) past it
    assert RC.surface_height(g, RC.Pt(100, 100)) == pytest.approx(132.0)
    assert RC.surface_height(g, RC.Pt(100, 200)) == pytest.approx(96.0)
    assert RC.surface_height(g, RC.Pt(100, 60)) == pytest.approx(132.0)
    g2 = RC.RoofGeom.from_record(_roof())
    assert g2.form == "gable"


def test_an_unclipped_shed_builds_one_slab_and_no_degenerate_plane(fp3d):
    shed = fp3d.build_model(_doc([_roof(form="shed", span=(100.0, 0.0))]), furnishings=False, floors=False)
    gable = fp3d.build_model(_doc([_roof()]), furnishings=False, floors=False)
    rs = next(m for m in shed.meshes if m.name == "roofs")
    rg = next(m for m in gable.meshes if m.name == "roofs")
    assert len(rs.verts) == 8 and len(rg.verts) == 16          # one slab against two
    ys = sorted({round(float(-y), 3) for y in rs.verts[:, 1]})
    assert ys == [100.0, 200.0]
    assert not shed.notes


def test_a_hipped_sheds_end_descends_along_the_ridge_line(fp3d):
    """His porch roof: a shed with hipped ends, unclipped (it touches the
    house but overlaps no roof). The hip face is the triangle from the
    ridge end to the two extended corners; the corner on the ridge line
    sits on the HIP plane -- eaves height less the overhang's drop at the
    end of the extension -- not at ridge height, which made a flat shelf
    (iteration 5 of the house model). The clipped path's `surface_height`
    already says so; the unclipped corners now agree with it."""
    porch = _roof(form="shed", span=(96.0, 0.0), gable=[False, False], eaves_h_in=104.0,
                  ridge_h_in=128.0, overhang_in=[12.0, 0.0], ridge=[[0.0, 432.0], [720.0, 432.0]])
    model = fp3d.build_model(_doc([porch]), furnishings=False, floors=False)
    roof = next(m for m in model.meshes if m.name == "roofs").verts
    on_ridge_line = roof[abs(-roof[:, 1] - 432.0) < 1e-6]
    # the hip run is the mean of the spans, 48, and the hip's overhang the
    # mean of the overhangs, 6 (0248 sec2 item 6: the formula, not a setting)
    ext = 48.0 + 6.0
    xs = sorted({round(float(x), 3) for x in on_ridge_line[:, 0]})
    assert xs == [-ext, 0.0, 720.0, 720.0 + ext], xs
    drop = (128.0 - 104.0) / 48.0 * ext
    for x in (-ext, 720.0 + ext):
        zs = sorted({round(float(z), 3) for z in on_ridge_line[abs(on_ridge_line[:, 0] - x) < 1e-6][:, 2]})
        assert zs == [round(128.0 - drop - fp3d.ROOF_T, 3), round(128.0 - drop, 3)], (x, zs)
    for x in (0.0, 720.0):
        zs = sorted({round(float(z), 3) for z in on_ridge_line[abs(on_ridge_line[:, 0] - x) < 1e-6][:, 2]})
        assert zs == [128.0 - fp3d.ROOF_T, 128.0], (x, zs)
    # and the same shed with gable ends has no corner past its ridge
    gab = dict(porch, gable=[True, True])
    m2 = fp3d.build_model(_doc([gab]), furnishings=False, floors=False)
    r2 = next(m for m in m2.meshes if m.name == "roofs").verts
    assert sorted({round(float(x), 3) for x in r2[:, 0]}) == [0.0, 720.0]


def test_a_shed_dormer_gets_a_side_at_both_ends(fp3d):
    """A shed dormer's high edge sits ON the host plane, so neither ridge
    end stands above the host and the face finder, which took the end
    standing highest, built one side only (0248 sec2 item 1). Both ends
    are faces now: a side at each end, from the host up to the shed's
    own slope."""
    host = _roof("rf_host", span=(100.0, 100.0), ridge_h_in=150.0)
    # the dormer: ridge along x at y=150, where the host is 96 + 0.54*50 = 123;
    # its plane descends toward the eaves (the left side, +y) to 96 at y=200
    dormer = _roof("rf_shed", form="shed", span=(50.0, 0.0), host="rf_host",
                   ridge=[[80.0, 150.0], [160.0, 150.0]], eaves_h_in=110.0, ridge_h_in=123.0)
    model = fp3d.build_model(_doc([host, dormer]), furnishings=False, floors=False)
    assert not model.notes, model.notes
    walls = next(m for m in model.meshes if m.name == "walls:exterior").verts
    t = fp3d.WALL_T.get("exterior", 6.0)
    xs = sorted({round(float(x), 3) for x in walls[:, 0]})
    # both end lines, each with its thickness inward along the ridge
    assert 80.0 in xs and round(80.0 + t, 3) in xs and 160.0 in xs and round(160.0 - t, 3) in xs, xs
    for x in (80.0, 160.0):
        side = walls[abs(walls[:, 0] - x) < 1e-6]
        assert side.size and side[:, 2].max() > 110.0 and side[:, 2].min() > 90.0   # an inch into the host
    # the face finder is the fix, not the form: the same dormer written the
    # old way, a gable with a 1in right strip, gets both ends too now
    legacy = dict(dormer, span_in=[50.0, 1.0])
    legacy.pop("form")
    m2 = fp3d.build_model(_doc([host, legacy]), furnishings=False, floors=False)
    w2 = next(m for m in m2.meshes if m.name == "walls:exterior").verts
    xs2 = {round(float(x), 3) for x in w2[:, 0]}
    assert 80.0 in xs2 and 160.0 in xs2


# ---------------------------------------------------------------------------
# plan C: the generated side or face yields to a house wall on its line
# ---------------------------------------------------------------------------
def _wall(wid, level, a, b, vx, openings=()):
    return {"id": wid, "level": level, "v1": a, "v2": b, "type": "exterior", "openings": list(openings)}


def test_a_cheek_on_a_house_walls_line_is_not_generated_and_the_wall_climbs(fp3d):
    """A gable dormer whose left cheek line (x=170) carries a house wall:
    the wall climbs into the dormer (as before) and no cheek box stands
    on that line; the right cheek (x=230), with no wall, is generated as
    before. The control: the same dormer with no walls gets both."""
    host = _roof("rf_host", span=(100.0, 100.0), ridge_h_in=150.0, ridge=[[0.0, 100.0], [400.0, 100.0]])
    dormer = _roof("rf_d", host="rf_host", span=(30.0, 30.0), ridge=[[200.0, 190.0], [200.0, 125.926]],
                   eaves_h_in=116.0, ridge_h_in=136.0, marker_end=0)
    vx = [{"id": "a", "level": "L1", "x": 170.0, "y": 150.0}, {"id": "b", "level": "L1", "x": 170.0, "y": 200.0}]
    walls = [_wall("w1", "L1", "a", "b", vx)]
    with_wall = fp3d.build_model(_doc([host, dormer], walls, vx), furnishings=False, floors=False)
    without = fp3d.build_model(_doc([host, dormer]), furnishings=False, floors=False)
    t = fp3d.WALL_T.get("exterior", 6.0)

    def cheek_boxes(model, x_line, inward):
        v = next(m for m in model.meshes if m.name == "walls:exterior").verts
        # the generated cheek's inward face is t from the line; a house wall's
        # faces are t/2 either side -- so the inward face is the cheek's own;
        # and behind the face band (y 184..190), whose boxes step along x too
        return v[(abs(v[:, 0] - (x_line + inward * t)) < 1e-6) & (-v[:, 1] < 184.0 - 1e-6)]

    assert len(cheek_boxes(without, 170.0, +1)) > 0 and len(cheek_boxes(without, 230.0, -1)) > 0
    assert len(cheek_boxes(with_wall, 170.0, +1)) == 0, "a cheek was generated on the wall's line"
    assert len(cheek_boxes(with_wall, 230.0, -1)) > 0
    # and the wall is there, climbing into the dormer (its top at the dormer plane less the cap)
    v = next(m for m in with_wall.meshes if m.name == "walls:exterior").verts
    on_wall = v[(abs(v[:, 0] - 170.0) < t / 2 + 1e-6) & (-v[:, 1] > 160.0) & (-v[:, 1] < 191.0)]
    assert on_wall.size and on_wall[:, 2].max() > 116.0 - fp3d.WALL_CAP_BELOW_ROOF_IN - 1e-6


def test_a_face_on_a_house_walls_line_is_not_generated_either(fp3d):
    """The dormer-gable-check geometry with a house wall on the face line
    y=190: no generated face; the wall climbs. Its windows show, which is
    the point (0248 sec2 item 2)."""
    host = _roof("rf_host", span=(100.0, 100.0), ridge_h_in=150.0, ridge=[[0.0, 100.0], [400.0, 100.0]])
    dormer = _roof("rf_d", host="rf_host", span=(30.0, 30.0), ridge=[[200.0, 190.0], [200.0, 125.926]],
                   eaves_h_in=116.0, ridge_h_in=136.0, marker_end=0)
    vx = [{"id": "a", "level": "L1", "x": 150.0, "y": 190.0}, {"id": "b", "level": "L1", "x": 250.0, "y": 190.0}]
    walls = [_wall("w1", "L1", "a", "b", vx, [{"id": "o1", "kind": "window", "code": "2030",
                                               "anchor": {"from": "v1", "offset_in": 40.0}, "sill_in": 110.0}])]
    with_wall = fp3d.build_model(_doc([host, dormer], walls, vx), furnishings=False, floors=False)
    without = fp3d.build_model(_doc([host, dormer]), furnishings=False, floors=False)
    t = fp3d.WALL_T.get("exterior", 6.0)

    def face_boxes(model):
        v = next(m for m in model.meshes if m.name == "walls:exterior").verts
        return v[abs(-v[:, 1] - (190.0 - t)) < 1e-6]          # the face's inward side

    assert len(face_boxes(without)) > 0
    assert len(face_boxes(with_wall)) == 0, "a face was generated on the wall's line"
    # the window is cut out of the climbing wall: a ray through the opening meets nothing
    import numpy as np
    walls_mesh = next(m for m in with_wall.meshes if m.name == "walls:exterior")
    verts, faces = walls_mesh.verts, walls_mesh.faces
    a = np.array([200.0, -195.0, 125.0])
    b = np.array([200.0, -185.0, 125.0])
    d = b - a
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = a - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    q = np.cross(tv, e1)
    w = np.einsum("j,ij->i", d, q) * inv
    tt = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9) & (tt >= 0) & (tt <= 1)
    assert int(hit.sum()) == 0, "the window in the climbing wall is covered"


def test_the_promoted_dormer_fixtures_are_unchanged_by_plan_c(fp3d):
    """R2's dormer face stands past the eaves wall (6in, more than half a
    thickness) and R3's on bare roof; the dormer-gable-check fixture has
    no walls under its dormer: none has a wall on a generated line, so the
    walls meshes are byte-identical with the yield switched off."""
    for name in ("short-angle-roofR2.json", "short-angle-roofR3.json", "dormer-gable-check.json"):
        doc = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        on = fp3d.build_model(doc, furnishings=False, floors=False)
        orig = fp3d._on_a_wall
        try:
            fp3d._on_a_wall = lambda *a, **k: False
            off = fp3d.build_model(doc, furnishings=False, floors=False)
        finally:
            fp3d._on_a_wall = orig
        a = next(m for m in on.meshes if m.name == "walls:exterior").verts
        b = next(m for m in off.meshes if m.name == "walls:exterior").verts
        assert a.shape == b.shape and (a == b).all(), name


def test_a_sheds_ends_are_never_joined_so_the_host_keeps_its_ground_beside_a_shed_dormer(fp3d):
    """The house model's shed dormer (iteration 6): its two ends stand
    inside the main roof, so the clip treated them as joined ends and ran
    the shed's plane sideways across the main -- a phantom, pruned to
    blank ground, and the main lost its whole front strip beside the
    dormer (147 x 72 in at the right end, measured). A shed's ends are
    never joined: the main keeps every inch beside the dormer, the shed
    draws its own footprint, and a GABLE dormer's back end is still joined
    (`test_roof_dormer.py` pins that)."""
    RC = fp3d.ROOFCLIP
    main = _roof("rf_main", span=(156.0, 156.0), eaves_h_in=36.0, ridge_h_in=140.0,
                 ridge=[[0.0, 156.0], [846.0, 156.0]])
    y_top = 170.0
    top_h = 140.0 - (104.0 / 156.0) * (y_top - 156.0)
    shed = _roof("rf_shed", form="shed", span=(312.0 - y_top, 0.0), host="rf_main",
                 ridge=[[350.0, y_top], [494.0, y_top]], eaves_h_in=108.0, ridge_h_in=top_h)
    geoms = {r["id"]: RC.RoofGeom.from_record(r) for r in (main, shed)}
    per = RC.compute_roof_clips(list(geoms.values()))
    assert per[id(geoms["rf_shed"])].ext == (0.0, 0.0)
    region = per[id(geoms["rf_main"])].region
    assert region is not None

    def area_in(x0, x1, y0, y1):
        box = [RC.Pt(x0, y0), RC.Pt(x1, y0), RC.Pt(x1, y1), RC.Pt(x0, y1)]
        total = 0.0
        for cell in region.cells:
            piece = RC._convex_intersection(cell, box)
            if piece:
                total += RC._area(piece)
        return total

    # the main's ground right of the dormer, left of it, and the strip under the dormer's face
    assert area_in(699.0, 846.0, 240.0, 312.0) == pytest.approx(147.0 * 72.0, abs=1.0)
    assert area_in(0.0, 124.0, 240.0, 312.0) == pytest.approx(124.0 * 72.0, abs=1.0)
    assert area_in(350.0, 494.0, 240.0, 312.0) == pytest.approx(0.0, abs=1.0)        # the shed's
    shed_region = per[id(geoms["rf_shed"])].region
    assert shed_region is not None
    xs = [p.x() for cell in shed_region.cells for p in cell]
    assert min(xs) >= 350.0 - 1e-6 and max(xs) <= 494.0 + 1e-6, "the shed ran sideways"
    assert not per[id(geoms["rf_main"])].warnings and not per[id(geoms["rf_shed"])].warnings

