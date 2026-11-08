"""A room's CEILING is built in 3D (Patrick, 2026-11-06: "there are no
ceilings/floors over the 1st floor"). An enclosed interior room gets a ceiling
slab at the top of its storey -- the attic floor over a 1½-storey -- so from
inside the attic the room below is closed off, not open to the ground. A porch
(exterior) room is open above and gets none. `fp3d.py` is loaded by path.
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
    spec = importlib.util.spec_from_file_location("fp3d_ceiling_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(category="interior", ceiling_in=None):
    V = [{"id": "a", "x": 0.0, "y": 0.0}, {"id": "b", "x": 120.0, "y": 0.0},
         {"id": "c", "x": 120.0, "y": 120.0}, {"id": "d", "x": 0.0, "y": 120.0}]
    room = {"id": "r1", "level": "L1", "category": category,
            "outline": [{"v": "a"}, {"v": "b"}, {"v": "c"}, {"v": "d"}]}
    if ceiling_in is not None:
        room["ceiling_in"] = ceiling_in
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": [{"id": "L1", "name": "L1", "elevation_in": 0.0,
                                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": V, "walls": [], "rooms": [room], "furnishings": [], "groups": []}


def _mesh(model, name):
    return next((m for m in model.meshes if m.name == name), None)


def test_an_interior_room_gets_a_ceiling_at_the_storey_top(fp3d):
    model = fp3d.build_model(_doc("interior"), furnishings=False)
    ceil = _mesh(model, "ceilings")
    assert ceil is not None, "no ceiling slab was built for the interior room"
    z = np.asarray(ceil.verts)[:, 2]
    # the ceiling's underside is the storey top (96); it sits just above it
    assert float(z.min()) == pytest.approx(96.0)
    assert 96.0 < float(z.max()) <= 98.0
    # and it covers the room, like the floor does
    assert _mesh(model, "floors") is not None


def test_the_ceiling_follows_a_room_ceiling_height(fp3d):
    model = fp3d.build_model(_doc("interior", ceiling_in=108.0), furnishings=False)
    z = np.asarray(_mesh(model, "ceilings").verts)[:, 2]
    assert float(z.min()) == pytest.approx(108.0)      # the room's own ceiling


def test_an_exterior_room_has_no_ceiling(fp3d):
    model = fp3d.build_model(_doc("exterior"), furnishings=False)
    assert _mesh(model, "ceilings") is None            # a porch is open above


def test_floors_off_builds_no_ceiling(fp3d):
    model = fp3d.build_model(_doc("interior"), furnishings=False, floors=False)
    assert _mesh(model, "ceilings") is None


def _doc_under_roof():
    """The room of `_doc`, now under a low gable roof whose eaves dip below the
    storey top (96). A flat ceiling at 96 would poke through the roof."""
    doc = _doc("interior")
    doc["roofs"] = [{
        "id": "rf1", "level": "L1", "ridge": [[-30, 60], [150, 60]],
        "eaves_h_in": 48.0, "ridge_h_in": 72.0, "overhang_in": [0, 0],
        "span_in": [140, 140], "gable": [True, True], "marker_end": 1}]
    return doc


def _doc_gable_with_short_upper_wall():
    """A 1½-storey box whose L2 gable wall ENDS short of the L1 gable (the upper
    floor is set back from the back eave). Patrick, 2026-11-08: a thin vertical
    hole appeared in the gable at the end of the L2 wall. The L1 gable wall below
    must climb the whole gable there; it was wrongly capped at the L2 base over a
    sliver because a header/pier piece straddled the end of the storey above and
    `above_bounds` judged the whole piece by its centroid."""
    V = [{"id": "a", "x": 0.0, "y": 0.0}, {"id": "b", "x": 120.0, "y": 0.0},
         {"id": "c", "x": 120.0, "y": 120.0}, {"id": "d", "x": 0.0, "y": 120.0},
         {"id": "e", "x": 0.0, "y": 20.0}, {"id": "f", "x": 120.0, "y": 20.0}]
    def wall(i, v1, v2, lvl):
        return {"id": f"w{i}", "level": lvl, "v1": v1, "v2": v2, "type": "exterior"}
    walls = [
        wall(1, "a", "d", "L1"),   # the L1 gable wall at x=0 (full depth y 0..120)
        wall(2, "a", "b", "L1"), wall(3, "b", "c", "L1"), wall(4, "c", "d", "L1"),
        wall(5, "e", "d", "L2"),   # the L2 gable wall at x=0 -- ENDS at y=20
        wall(6, "e", "f", "L2"),   # the L2 back wall (across the gable) at y=20
        wall(7, "f", "c", "L2"), wall(8, "c", "d", "L2")]
    room2 = {"id": "r2", "level": "L2", "category": "interior",
             "outline": [{"v": "e"}, {"v": "f"}, {"v": "c"}, {"v": "d"}]}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "vertices": V, "walls": walls, "rooms": [room2],
            "furnishings": [], "groups": [],
            "levels": [{"id": "L1", "name": "L1", "elevation_in": 0.0,
                        "height_in": 96.0, "kind": "storey", "reference": False},
                       {"id": "L2", "name": "L2", "elevation_in": 96.0,
                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "roofs": [{"id": "rf1", "level": "L1", "ridge": [[0, 60], [120, 60]],
                       "eaves_h_in": 108.0, "ridge_h_in": 180.0, "overhang_in": [0, 0],
                       "span_in": [60, 60], "gable": [True, True], "marker_end": 1}]}


def _ray_hits_x(model, mesh_name, y_plan, z, x0=-10.0, x1=10.0):
    """A ray across the gable wall's thickness (the wall is at plan x=0, so world
    x≈0) at world (y=-y_plan, z): does it meet any triangle of `mesh_name`?"""
    m = _mesh(model, mesh_name)
    if m is None:
        return 0
    V = np.asarray(m.verts)
    F = np.asarray(m.faces)
    a = np.array([x0, -y_plan, z])
    d = np.array([x1 - x0, 0.0, 0.0])
    v0, v1, v2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = a - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    q = np.cross(tv, e1)
    ww = np.einsum("j,ij->i", d, q) * inv
    tt = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-6) & (ww >= -1e-6) & (u + ww <= 1 + 1e-6) & (tt >= 0) & (tt <= 1)
    return int(hit.sum())


def test_no_gable_hole_at_the_end_of_an_upper_wall(fp3d):
    """Regression (Patrick, 2026-11-08): the L1 gable must be SOLID just past the
    end of the L2 gable wall (y<20), where the roof (here ~120 at y=10) still
    rises above the L2 base (96). The sliver z=96..roof was an open hole because a
    straddling piece was capped at the L2 base with nothing climbing the overhang."""
    model = fp3d.build_model(_doc_gable_with_short_upper_wall(), furnishings=False, floors=False)
    # y=10 is past the L2 wall's end (y=20); the roof there is ~120, L2 base is 96
    assert _ray_hits_x(model, "walls:exterior", 10.0, 110.0) > 0, "gable hole past the L2 wall end"
    assert _ray_hits_x(model, "walls:exterior", 10.0, 100.0) > 0, "gable hole just above the L2 base"
    # and the gable below the L2 base is of course still solid
    assert _ray_hits_x(model, "walls:exterior", 10.0, 50.0) > 0


def test_the_ceiling_does_not_poke_through_the_roof(fp3d):
    """Patrick, 2026-11-07: "the ceiling of a floor needs to be the lesser of the
    roof or the ceiling height." Under a low roof the ceiling is clamped to the
    roof underside, so no ceiling vertex rises above the roof surface over it."""
    import floorplanner.roofclip as rc
    doc = _doc_under_roof()
    model = fp3d.build_model(doc, furnishings=False)
    ceil = _mesh(model, "ceilings")
    assert ceil is not None
    geom = rc.RoofGeom.from_record(doc["roofs"][0], span_fallback=144.0)
    fp = rc.footprint_polygon(geom)
    verts = np.asarray(ceil.verts)
    # the flat ceiling would sit at 96; the roof over the room dips well below it
    assert float(verts[:, 2].max()) < 96.0
    for x, y, z in verts:
        pt = rc.Pt(float(x), -float(y))            # world -> plan
        if rc._contains(fp, pt):
            surf = float(rc.surface_height(geom, pt))
            assert z <= surf + 1e-6                 # at or under the roof surface
