"""0248-report.md sec3 plan B, on Patrick's word ("Implement plan B and D
from 0248"): OPENINGS ON A DORMER RECORD, cut into its generated face.

A dormer standing on its host roof has a generated face (0245) and, for
a shed dormer, a generated front edge (0244); until now both were blank
(0248 sec2 item 4). The record now carries `openings` -- the same
records a wall carries -- dimensioned along the face like a wall: `v1`
its left end, `v2` its right, `center` its middle; sill and head above
the dormer's level base. The 3D builder cuts them in: the piece under
the sill, the piece over the head, nothing between.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.validate import schema_errors
from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_openings_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(roofs):
    return {"format": "floorplanner-design", "version": 6, "units": "inches", "settings": {},
            "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0, "height_in": 96.0,
                        "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [], "groups": [], "roofs": list(roofs)}


HOST = {"id": "rf_host", "level": "L1", "ridge": [[0.0, 100.0], [400.0, 100.0]], "eaves_h_in": 96.0,
        "ridge_h_in": 150.0, "overhang_in": [0.0, 0.0], "span_in": [100.0, 100.0], "eaves_bind": "manual",
        "gable": [True, True], "marker_end": 1}
# the dormer-gable-check geometry: face at y=190 on the host (101.4 there), ridge 136, eaves 116, 30 each side
DORMER = {"id": "rf_d", "level": "L1", "ridge": [[200.0, 190.0], [200.0, 125.926]], "eaves_h_in": 116.0,
          "ridge_h_in": 136.0, "overhang_in": [0.0, 0.0], "span_in": [30.0, 30.0], "eaves_bind": "manual",
          "gable": [True, True], "marker_end": 0, "host": "rf_host"}
WINDOW = {"id": "o1", "kind": "window", "code": "2412", "anchor": {"from": "center", "offset_in": 0.0},
          "sill_in": 108.0}                                     # 24 wide, 12 tall: 108..120, x 188..212


def _seg_hits(mesh, a, b):
    verts, faces = mesh.verts, mesh.faces
    a = np.array(a, float)
    b = np.array(b, float)
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
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9) & (t >= 0) & (t <= 1)
    return int(hit.sum())


def _face_ray(x, z):
    """A ray through the dormer's face plane (y=190, its thickness inward to 184) at world (x, z)."""
    return (x, -195.0, z), (x, -181.0, z)


# ---------------------------------------------------------------------------
# the record
# ---------------------------------------------------------------------------
def test_openings_are_legal_on_a_dormer_and_on_nothing_else():
    assert schema_errors(_doc([HOST, dict(DORMER, openings=[WINDOW])])) == []
    bare = dict(HOST, openings=[WINDOW])
    assert schema_errors(_doc([bare])) != [], "a roof with no host cannot carry openings"
    assert schema_errors(_doc([HOST, DORMER])) == []


def test_the_openings_round_trip_through_the_document(scene):
    doc = _doc([HOST, dict(DORMER, openings=[WINDOW])])
    rep = {}
    apply_design_to_scene(scene, doc, report=rep)
    items = {it.p1.y(): it for it in scene.items() if isinstance(it, RoofItem)}
    dormer = items[190.0]
    assert dormer.openings == [WINDOW]
    assert items[100.0].openings == []
    out = design_from_scene(scene).to_dict()
    recs = {r["ridge"][0][1]: r for r in out["roofs"]}
    assert recs[190.0]["openings"] == [WINDOW]
    assert "openings" not in recs[100.0]
    assert schema_errors(out) == []
    plain = RoofItem(QPointF(0, 0), QPointF(10, 0))
    assert plain.openings == []


# ---------------------------------------------------------------------------
# the face
# ---------------------------------------------------------------------------
def test_a_window_is_cut_into_the_generated_face(fp3d):
    """The dormer's face at y=190 stands on the host (101.4) up to the rake
    (136 at the ridge, 116 at the sides). A 24 x 12 window centred on the
    face, sill 108: rays through the face plane inside the window hit no
    wall; rays under the sill, over the head and beside the window hit."""
    with_window = fp3d.build_model(_doc([HOST, dict(DORMER, openings=[WINDOW])]), furnishings=False, floors=False)
    without = fp3d.build_model(_doc([HOST, DORMER]), furnishings=False, floors=False)
    w_with = next(m for m in with_window.meshes if m.name == "walls:exterior")
    w_without = next(m for m in without.meshes if m.name == "walls:exterior")
    inside = [_face_ray(200.0, 114.0), _face_ray(190.0, 110.0), _face_ray(210.0, 118.0)]
    around = [_face_ray(200.0, 105.0),      # under the sill (the host is at 101.4)
              _face_ray(200.0, 124.0),      # over the head, under the ridge (136)
              _face_ray(216.0, 114.0),      # beside the window, right
              _face_ray(184.0, 114.0)]      # beside, left
    for a, b in inside:
        assert _seg_hits(w_with, a, b) == 0, (a, b)
        assert _seg_hits(w_without, a, b) > 0, (a, b)
    for a, b in around:
        assert _seg_hits(w_with, a, b) > 0, (a, b)
    assert not with_window.notes


def test_a_window_on_a_shed_dormers_front_edge(fp3d):
    """A shed dormer's face is its low front edge (`_dormer_cheeks`, side 0).
    Ridge along x at y=150 on the host (123 there), its plane down to 110
    at y=200, where the host is at 96 (99.2 six inches in, at the cheek's
    inner face): a band of front edge 14 in tall at its face. A 20 x 8
    window from v1 (ridge[0]'s end) 10 in in, sill 100: open 100..108 in
    x 90..110; the sill piece (the host up to 100) and the head piece
    (108..109.5) stand, and so does the edge beside it."""
    shed = {"id": "rf_s", "level": "L1", "ridge": [[80.0, 150.0], [160.0, 150.0]], "eaves_h_in": 110.0,
            "ridge_h_in": 123.0, "overhang_in": [0.0, 0.0], "span_in": [50.0, 0.0], "eaves_bind": "manual",
            "gable": [True, True], "marker_end": 1, "host": "rf_host", "form": "shed"}
    win = {"id": "o2", "kind": "window", "code": "2008", "anchor": {"from": "v1", "offset_in": 10.0},
           "sill_in": 100.0}
    with_win = fp3d.build_model(_doc([HOST, dict(shed, openings=[win])]), furnishings=False, floors=False)
    without = fp3d.build_model(_doc([HOST, shed]), furnishings=False, floors=False)
    w_with = next(m for m in with_win.meshes if m.name == "walls:exterior")
    w_without = next(m for m in without.meshes if m.name == "walls:exterior")

    def ray(x, z):
        return (x, -205.0, z), (x, -191.0, z)       # through the front edge y=200, t inward

    for x in (95.0, 105.0):
        assert _seg_hits(w_with, *ray(x, 103.0)) == 0, x
        assert _seg_hits(w_without, *ray(x, 103.0)) > 0, x
        assert _seg_hits(w_with, *ray(x, 99.0)) > 0, (x, "the sill piece")
        assert _seg_hits(w_with, *ray(x, 109.0)) > 0, (x, "the head piece")
    for x in (85.0, 115.0, 150.0):
        assert _seg_hits(w_with, *ray(x, 103.0)) > 0, x
    assert not with_win.notes


def test_an_unreadable_opening_is_skipped_and_the_face_is_whole(fp3d):
    bad = dict(DORMER, openings=[{"id": "o9", "kind": "window", "code": "huge",
                                  "anchor": {"from": "v1", "offset_in": 0.0}}])
    model = fp3d.build_model(_doc([HOST, bad]), furnishings=False, floors=False)
    plain = fp3d.build_model(_doc([HOST, DORMER]), furnishings=False, floors=False)
    a = next(m for m in model.meshes if m.name == "walls:exterior").verts
    b = next(m for m in plain.meshes if m.name == "walls:exterior").verts
    assert a.shape == b.shape and (a == b).all()


def test_the_promoted_dormer_fixtures_carry_no_openings_and_build_as_before(fp3d):
    import json
    for name in ("short-angle-roofR2.json", "short-angle-roofR3.json", "dormer-gable-check.json"):
        doc = json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))
        assert all("openings" not in r for r in doc["roofs"])
        model = fp3d.build_model(doc, furnishings=False, floors=False)
        assert not model.notes, name
