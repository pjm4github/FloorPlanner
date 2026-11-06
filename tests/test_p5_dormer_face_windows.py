"""P5 of the 1½-storey arc (0294 §3): a dormer's OWN face window is cut into the
CLIMBING WALL on its face.

Before P5, the dormer's `openings` cut only the GENERATED face; where a house wall
stands on the face line the face yields (`_on_a_wall`) and generated 0 triangles,
so a face window over a wall was a no-op -- 0292 measured a 0-triangle change, and
his gable-end windows never rendered. P5 projects the dormer's face openings onto
that wall's climbing pieces: the band is a void, its head unclamped (it sits above
the storey top), its header climbing to the dormer surface.

`fp3d.py` is loaded by path, like the other viewer tests.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_p5_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(dormer_window):
    """A dormer `d` (host `h`) whose face at y=240 sits on the house wall `w1`
    (160,240)-(240,240). The window, when present, is the DORMER's own face
    opening (not a wall opening), high in the gable (sill 195, head ~225)."""
    V = [{"id": "wa", "x": 160.0, "y": 240.0}, {"id": "wb", "x": 240.0, "y": 240.0}]
    wall = {"id": "w1", "level": "L1", "v1": "wa", "v2": "wb",
            "type": "exterior", "openings": []}
    ops = []
    if dormer_window:
        ops = [{"id": "fw", "kind": "window", "code": "2030",
                "anchor": {"from": "center", "offset_in": 0.0}, "sill_in": 195.0}]
    host = {"id": "h", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "d", "level": "L1", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "h", "openings": ops}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": V, "walls": [wall], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [host, dormer]}


def _ext(model):
    return next(m for m in model.meshes if m.name == "walls:exterior")


def _tris(model):
    return sum(len(m.faces) for m in model.meshes if m.faces is not None)


def test_a_dormer_face_window_over_a_wall_changes_the_mesh(fp3d):
    """0294 §3's fail-first: 0292 measured a 0-triangle change (the face yielded
    and nothing was cut). The dormer face window must now cut the climbing wall,
    so the triangle count moves."""
    base = _tris(fp3d.build_model(_doc(dormer_window=False), furnishings=False, floors=False))
    withw = _tris(fp3d.build_model(_doc(dormer_window=True), furnishings=False, floors=False))
    assert withw != base, "the dormer face window did not cut the climbing wall (0292's 0)"


def test_the_dormer_face_window_is_a_void_in_the_climbing_wall(fp3d):
    model = fp3d.build_model(_doc(dormer_window=True), furnishings=False, floors=False)
    verts, faces = _ext(model).verts, _ext(model).faces
    # a ray across the wall thickness, through the window (x=200, z=205 in the
    # 195..225 opening, well above the 96 storey top), must meet no triangle
    a = np.array([200.0, -235.0, 205.0])
    b = np.array([200.0, -245.0, 205.0])
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
    ww = np.einsum("j,ij->i", d, q) * inv
    tt = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (ww >= -1e-9) & (u + ww <= 1 + 1e-9) & (tt >= 0) & (tt <= 1)
    assert int(hit.sum()) == 0, "the dormer face window is covered, not a void"


def test_the_gable_stays_closed_below_and_above_the_face_window(fp3d):
    """The window is a void; the wall is solid below the sill and above the head
    (the climb to the dormer surface continues past the window)."""
    verts = _ext(fp3d.build_model(_doc(dormer_window=True), furnishings=False, floors=False)).verts
    col = verts[(abs(verts[:, 0] - 200.0) < 14.0) & (abs(verts[:, 1] + 240.0) < 14.0)]
    assert len(col)
    assert float(col[:, 2].min()) < 10.0           # solid down to the floor
    assert float(col[:, 2].max()) > 220.0          # climbs to the dormer surface above
