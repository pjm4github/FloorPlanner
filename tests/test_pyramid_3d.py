"""0367 stage 2 -- the pyramid roof in 3D (`fp3d.build_model`).

A pyramid-roof furnishing is built as its own slab of triangular faces, reading
`pyramid_geometry` (the same calculator the editor and the plan symbol use --
condition C1), drawn WHOLE over whatever is there (the weld is stage 3). A post
under one rises to its underside; a pyramid that cannot be built still loads, is
drawn RED, and says why in `model.notes` (C5). Qt-free, fp3d loaded by path.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]

# the default hexagon with manual eaves at 96: apex = 96 + 72*10/12 = 156;
# eave edge = 96 - 12*10/12 = 86; at a wall-line corner the surface is the eaves
APEX_Z, EAVES_Z, EAVE_EDGE_Z = 156.0, 96.0, 86.0
ROOF_T = 4.0


def _load_fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_pyramid_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fp3d():
    return _load_fp3d()


def _pyramid(state=None, pos=(200.0, 200.0), rotation=0.0):
    st = {"sides": 6, "eaves_bind": "manual", "eaves_h_in": 96.0}
    st.update(state or {})
    return {"id": "py1", "kind": "pyramid_roof", "level": "L1",
            "pos": list(pos), "rotation": rotation, "state": st}


def _doc(furnishings, rooms=(), vertices=()):
    return {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}],
            "vertices": list(vertices), "walls": [], "rooms": list(rooms),
            "furnishings": list(furnishings), "roofs": []}


def _roof_verts(model):
    import numpy as np
    parts = [m.verts for m in model.meshes if m.name == "roofs"]
    return np.vstack(parts) if parts else np.zeros((0, 3))


# -- the face slab ------------------------------------------------------------
def test_a_pyramid_builds_a_roof_slab_whole(fp3d):
    model = fp3d.build_model(_doc([_pyramid()]), floors=False)
    roofs = [m for m in model.meshes if m.name == "roofs"]
    assert roofs, "the pyramid drew no roof mesh"
    # six faces, each a ROOF_T slab over a triangle: 6 verts, 8 triangles
    total_faces = sum(len(m.faces) for m in roofs)
    assert total_faces == 6 * 8
    v = _roof_verts(model)
    assert v[:, 2].max() == pytest.approx(APEX_Z)                 # apex
    assert v[:, 2].min() == pytest.approx(EAVE_EDGE_Z - ROOF_T)   # eave underside
    assert not any("cannot be built" in n for n in model.notes)


def test_the_apex_stands_over_the_centre(fp3d):
    import numpy as np
    model = fp3d.build_model(_doc([_pyramid(pos=(200.0, 240.0))]), floors=False)
    v = _roof_verts(model)
    top = v[int(np.argmax(v[:, 2]))]
    # doc y is flipped into the mesh frame (x, -y)
    assert top[0] == pytest.approx(200.0) and top[1] == pytest.approx(-240.0)


def test_it_builds_with_no_ridge_roofs_in_the_document(fp3d):
    model = fp3d.build_model(_doc([_pyramid()]), floors=False, roofs=False)
    assert [m for m in model.meshes if m.name == "roofs"], \
        "a pyramid is a furnishing; it builds even with roofs off"


# -- C5: a broken pyramid draws red and is noted ------------------------------
def test_a_flat_pyramid_is_drawn_red_and_noted(fp3d):
    model = fp3d.build_model(_doc([_pyramid({"pitch_12": 0.0})]), floors=False)
    assert [m for m in model.meshes if m.name == "pyramid_error"], \
        "a pyramid that cannot be built is drawn red"
    assert any("cannot be built" in n for n in model.notes)
    assert not [m for m in model.meshes if m.name == "roofs"]


# -- R3 / E1: a post under a pyramid rises to its underside -------------------
def _post(pos):
    return {"id": "p1", "kind": "post", "level": "L1", "pos": list(pos),
            "rotation": 0.0}


def _post_top(model):
    import numpy as np
    parts = [m.verts for m in model.meshes if m.name == "furnishings:wood"]
    return float(np.vstack(parts)[:, 2].max()) if parts else None


def test_a_post_at_the_centre_rises_to_the_apex_underside(fp3d):
    model = fp3d.build_model(_doc([_pyramid(), _post((200.0, 200.0))]),
                             floors=False)
    assert _post_top(model) == pytest.approx(APEX_Z - ROOF_T, abs=0.5)


def test_a_post_at_a_wall_corner_rises_to_the_eaves_underside(fp3d):
    # a gazebo post (E1): on the wall line, under the eaves-start line
    import math
    pg = importlib.import_module("floorplanner.parametric.pyramid_geometry")
    corner = pg.wall_polygon(pg.normalize_state({"sides": 6}))[0]
    px, py = pg.to_plan((200.0, 200.0), 0.0, corner)
    model = fp3d.build_model(_doc([_pyramid(), _post((px, py))]), floors=False)
    assert _post_top(model) == pytest.approx(EAVES_Z - ROOF_T, abs=0.5)
    assert math.isclose(px, 200.0 + corner[0]) and math.isclose(py, 200.0 + corner[1])


# -- R3: the walls under a pyramid rise to it ---------------------------------
WALL_CAP = ROOF_T + 0.5          # WALL_CAP_BELOW_ROOF_IN: the slab + clearance


def _square_doc(with_pyramid=True, eaves=120.0):
    """A 100in square room on exterior walls, a square pyramid over it whose
    wall line sits on those walls. The walls are 96 tall; the eaves are higher,
    so an exterior wall RISES to the pyramid's surface."""
    corners = [("a", 150, 150), ("b", 250, 150), ("c", 250, 250), ("d", 150, 250)]
    verts = [{"id": i, "x": x, "y": y} for i, x, y in corners]
    edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]
    walls = [{"id": f"w{k}", "level": "L1", "v1": a, "v2": b, "type": "exterior"}
             for k, (a, b) in enumerate(edges)]
    rooms = [{"id": "r1", "level": "L1", "category": "interior", "ceiling_in": 96.0,
              "outline": [{"v": i} for i, _, _ in corners]}]
    furn = []
    if with_pyramid:
        furn = [_pyramid({"sides": 4, "inradius_in": 50.0, "eaves_bind": "manual",
                          "eaves_h_in": eaves, "overhang_in": 12.0})]
    return {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}],
            "vertices": verts, "walls": walls, "rooms": rooms,
            "furnishings": furn, "roofs": []}


def _ext_wall_top(fp3d, model):
    import numpy as np
    parts = [m.verts for m in model.meshes if m.name == "walls:exterior"]
    return float(np.vstack(parts)[:, 2].max()) if parts else None


def test_an_exterior_wall_rises_to_the_pyramid_surface(fp3d):
    model = fp3d.build_model(_square_doc(eaves=120.0), floors=False)
    top = _ext_wall_top(fp3d, model)
    # it climbs well above its own 96 to just under the pyramid surface: at the
    # wall's INNER edge (inside the eaves line) the surface is above the 120 eaves,
    # so the capped top lands near 118 (surface - WALL_CAP), not at 96
    assert top > 112.0, f"the wall did not climb into the pyramid ({top})"
    assert top < 125.0, f"the wall climbed past the pyramid surface ({top})"


def test_without_the_pyramid_the_same_wall_stays_at_its_own_height(fp3d):
    # C4 fail-first: take the pyramid away and the climb is gone -- the wall
    # stops at its own 96. This is the cut the climb test depends on.
    model = fp3d.build_model(_square_doc(with_pyramid=False), floors=False)
    assert _ext_wall_top(fp3d, model) == pytest.approx(96.0, abs=0.5)


def test_a_flat_pyramid_does_not_cap_the_walls(fp3d):
    # C5: a pyramid that cannot be built is red and holds nothing up
    model = fp3d.build_model(_square_doc() | {
        "furnishings": [_pyramid({"sides": 4, "inradius_in": 50.0,
                                  "eaves_bind": "manual", "eaves_h_in": 120.0,
                                  "pitch_12": 0.0})]}, floors=False)
    assert _ext_wall_top(fp3d, model) == pytest.approx(96.0, abs=0.5)


# -- R4: the weld (stage 3) ---------------------------------------------------
# a gable (ridge along x at y=200, eaves 96, ridge 150) with a square pyramid
# astride the ridge: apex 170 above the ridge, so the pyramid pokes up at the
# centre and dies into the gable toward its corners. E4.
def _astride_doc(weld="auto"):
    roof = {"id": "rf1", "level": "L1", "ridge": [[100, 200], [300, 200]],
            "eaves_h_in": 96.0, "ridge_h_in": 150.0, "span_in": [100, 100],
            "overhang_in": [12, 12], "gable": [True, True]}
    pyr = _pyramid({"sides": 4, "inradius_in": 60.0, "eaves_bind": "manual",
                    "eaves_h_in": 110.0, "pitch_12": 12.0, "overhang_in": 10.0,
                    "weld": weld})
    return {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [pyr],
            "roofs": [roof]}


def _top_surfaces_over(model, x, y):
    """The distinct UPWARD roof surfaces (interpolated z) standing over plan
    point (x, y) -- one per real surface, so a welded point has ONE and an
    un-welded overlap has two. Mesh frame is (x, -y)."""
    import numpy as np
    my = -y
    zs = []
    for m in model.meshes:
        if m.name not in ("roofs", "pyramid_error"):
            continue
        v, faces = m.verts, m.faces
        for a, b, c in faces:
            pa, pb, pc = v[a], v[b], v[c]
            # upward-facing only (prism-slab top caps), so bottoms/sides drop out
            n = np.cross(pb - pa, pc - pa)
            if n[2] <= 1e-6:
                continue
            d = ((pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1]))
            if abs(d) < 1e-9:
                continue
            wa = ((pb[1] - pc[1]) * (x - pc[0]) + (pc[0] - pb[0]) * (my - pc[1])) / d
            wb = ((pc[1] - pa[1]) * (x - pc[0]) + (pa[0] - pc[0]) * (my - pc[1])) / d
            wc = 1 - wa - wb
            if wa < -1e-6 or wb < -1e-6 or wc < -1e-6:
                continue
            zs.append(float(wa * pa[2] + wb * pb[2] + wc * pc[2]))
    zs.sort(reverse=True)
    out = []
    for z in zs:
        if not out or abs(out[-1] - z) > 1.0:
            out.append(z)
    return out


def test_weld_off_leaves_both_surfaces_whole(fp3d):
    # over the apex, the pyramid (170) AND the gable (150) are both drawn
    levels = _top_surfaces_over(fp3d.build_model(_astride_doc("off"), floors=False),
                                200.0, 200.0)
    assert len(levels) == 2
    assert levels[0] == pytest.approx(170.0, abs=1.0)   # pyramid apex
    assert levels[1] == pytest.approx(150.0, abs=2.0)   # gable ridge, under it


def test_weld_cuts_the_roof_under_the_pyramid(fp3d):
    # C4 fail-first: the cut removes the gable under the apex, leaving ONE
    # surface -- the higher pyramid. (weld off above leaves two.)
    levels = _top_surfaces_over(fp3d.build_model(_astride_doc("auto"), floors=False),
                                200.0, 200.0)
    assert len(levels) == 1
    assert levels[0] == pytest.approx(170.0, abs=1.0)


def test_weld_cuts_the_pyramid_where_the_roof_is_higher(fp3d):
    # near a pyramid corner (x=200+42,y=200) the gable is higher than the
    # pyramid, so the pyramid is cut there and only the gable stands
    x, y = 245.0, 200.0
    auto = _top_surfaces_over(fp3d.build_model(_astride_doc("auto"), floors=False), x, y)
    off = _top_surfaces_over(fp3d.build_model(_astride_doc("off"), floors=False), x, y)
    assert len(auto) == 1 and auto[0] == pytest.approx(150.0, abs=3.0)   # gable only
    assert len(off) == 2            # weld off: pyramid still drawn below the gable
