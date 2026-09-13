"""The 3D walls are CLIPPED TO THE ROOF -- Patrick's own instruction on
R5a's check, 2026-09-13, the authority for this change (0065-ruling.md
sec2, quoted as that ruling requires): *"The only minor change we need is
to clip the walls to the roof when viewing in 3D. At the moment the walls
stick up through the roof."*

`fp3d._wall_under_roofs` caps every solid piece of a wall at the surface
of the roof whose TERRITORY (R4d/R4g's visible region, or the whole
footprint of a lone roof) it lies under, exactly -- the wall quad is split
by the territory's cell edges and the roof's own plane-change lines, so
each piece's cap is one plane and the level sets at the piece's top and
base are found by exact interpolation, never sampled. A wall the roof does
not reach keeps its height; a plan whose roofs all clear their wall tops
builds byte-identically to a plan with no roofs at all.

Qt-free, like every fp3d test: the module is loaded by path.
"""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]


def _load_fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_wall_clip_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fp3d():
    return _load_fp3d()


# A 300x200 shell (tests/test_viewer_model.py's own), the ridge running the
# FULL length at plan y=100 so both gable walls stand under the ridge ends;
# eaves 80 / ridge 132 over 96in walls, span 100 either side -- the roof
# crosses the wall top at |perp| = (132 - 96) / 0.52 = 69.23in, the same
# closed form tests/test_roof_clip.py and test_roof_clip_trace.py use.
EAVES_H, RIDGE_H, SPAN, WALL_H = 80.0, 132.0, 100.0, 96.0
SLOPE = (RIDGE_H - EAVES_H) / SPAN
PERP_THRESH = (RIDGE_H - WALL_H) / SLOPE        # 69.230769...
EXT_T = 6.0                                     # fp3d's exterior wall thickness


def _roof(eaves_h=EAVES_H, ridge_h=RIDGE_H, ridge=((0, 100), (300, 100)),
          span=(SPAN, SPAN), rid="rf1", overhang=0.0):
    return {"id": rid, "level": "L1", "ridge": [list(ridge[0]), list(ridge[1])],
            "eaves_h_in": eaves_h, "ridge_h_in": ridge_h, "overhang_in": overhang,
            "span_in": list(span), "gable": [True, True]}


def _doc(roofs, extra_walls=(), openings=None):
    d = {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": WALL_H}],
         "vertices": [
             {"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 300, "y": 0},
             {"id": "v3", "x": 300, "y": 200}, {"id": "v4", "x": 0, "y": 200},
             {"id": "v5", "x": 500, "y": 0}, {"id": "v6", "x": 600, "y": 0}],
         "walls": [
             {"id": "w1", "level": "L1", "v1": "v1", "v2": "v2", "type": "exterior"},
             {"id": "w2", "level": "L1", "v1": "v2", "v2": "v3", "type": "exterior"},
             {"id": "w3", "level": "L1", "v1": "v3", "v2": "v4", "type": "exterior"},
             {"id": "w4", "level": "L1", "v1": "v4", "v2": "v1", "type": "exterior"},
         ] + list(extra_walls),
         "rooms": [], "furnishings": [], "roofs": list(roofs)}
    if openings:
        d["walls"][0]["openings"] = openings
    return d


def _wall_verts(model):
    parts = [m.verts for m in model.meshes if m.name.startswith("walls:")]
    assert parts, "no wall mesh built -- the check would be vacuous"
    return np.vstack(parts)


def _build(fp3d, doc, **kw):
    model = fp3d.build_model(doc, furnishings=False, floors=False, **kw)
    assert not model.notes, model.notes
    return model


def _surface_z(x_w, y_w):
    """The fixture roof's own top surface at a world point (plan y = -y_w),
    written out independently of roofclip: ridge at plan y=100."""
    return RIDGE_H - SLOPE * abs(-y_w - 100.0)


# --------------------------------------------------------------------------
# the instruction itself: nothing sticks up through the roof
# --------------------------------------------------------------------------
def test_no_wall_vertex_rises_above_the_roof_surface(fp3d):
    v = _wall_verts(_build(fp3d, _doc([_roof()])))
    over = [(x, y, z) for x, y, z in v if z > _surface_z(x, y) + 1e-6]
    assert not over, f"{len(over)} wall vertices above the roof, e.g. {over[:3]}"
    # positive control: without the roof the same walls reach their full height
    v0 = _wall_verts(_build(fp3d, _doc([]), roofs=False))
    assert v0[:, 2].max() == pytest.approx(WALL_H)


def test_the_gable_wall_top_follows_the_slope_and_flattens_under_the_ridge(fp3d):
    """The x=0 wall runs across the roof: capped at the eaves height at its
    two corners (plan y=0/200), rising along the slope to the wall top at
    |perp| = PERP_THRESH, and FLAT at the wall top from there to the ridge
    -- the roof clears the wall there, so the wall is not cut. Those three
    kinds of vertex must all exist, at the right heights."""
    v = _wall_verts(_build(fp3d, _doc([_roof()])))
    g = v[np.abs(v[:, 0]) <= EXT_T / 2 + 1e-6]          # the x=0 wall's own verts
    assert len(g) >= 8

    def has(y_w, z):
        return bool(np.any(np.isclose(g[:, 1], y_w, atol=1e-6)
                           & np.isclose(g[:, 2], z, atol=1e-6)))

    assert has(0.0, EAVES_H) and has(-200.0, EAVES_H), "corners not at the eaves"
    assert has(-(100.0 - PERP_THRESH), WALL_H), "no crossing vertex, low side"
    assert has(-(100.0 + PERP_THRESH), WALL_H), "no crossing vertex, high side"
    assert has(-100.0, WALL_H), "the wall under the ridge should stay at its top"
    assert not np.any(g[:, 2] > WALL_H + 1e-6)


def test_the_eaves_wall_with_no_overhang_is_capped_by_the_continued_plane(fp3d):
    """With overhang 0 the eave line lies ON the eaves wall's centreline, so
    its outer half is outside the footprint. It is still capped -- by the
    plane continued past the eave -- so no fin of wall stands beside the
    eave: every vertex of the plan y=0 wall sits on or under the plane."""
    v = _wall_verts(_build(fp3d, _doc([_roof()])))
    e = v[np.abs(v[:, 1]) <= EXT_T / 2 + 1e-6]           # the plan y=0 wall
    assert len(e) >= 8
    assert e[:, 2].max() <= EAVES_H + SLOPE * EXT_T / 2 + 1e-6
    assert e[:, 2].max() > EAVES_H - SLOPE * EXT_T / 2 - 1e-6, \
        "capped far below the eave -- the plane was not what did the capping"


# --------------------------------------------------------------------------
# what must NOT change
# --------------------------------------------------------------------------
def test_a_roof_that_clears_every_wall_top_builds_the_walls_byte_identically(fp3d):
    hi = _roof(eaves_h=100.0, ridge_h=140.0)
    with_roof = _wall_verts(_build(fp3d, _doc([hi])))
    without = _wall_verts(_build(fp3d, _doc([]), roofs=False))
    assert with_roof.shape == without.shape
    assert np.array_equal(with_roof, without)


def test_a_wall_the_roof_does_not_reach_keeps_its_height(fp3d):
    far = {"id": "w9", "level": "L1", "v1": "v5", "v2": "v6", "type": "exterior"}
    v = _wall_verts(_build(fp3d, _doc([_roof()], [far])))
    far_v = v[v[:, 0] > 400.0]
    assert len(far_v) == 8, "the far wall should be one plain box"
    assert far_v[:, 2].max() == pytest.approx(WALL_H)


def test_a_window_header_wholly_above_the_roof_is_gone_and_the_sill_wall_stays(fp3d):
    """On the eaves wall (roof at ~80in) a window with its head at 90in has
    a header piece 90..96 that lies entirely above the roof: dropped. Its
    under-sill piece (0..30) and the piers stay, all under the plane."""
    op = [{"id": "o1", "kind": "window", "code": "3050",
           "anchor": {"from": "start", "offset_in": 100}, "sill_in": 30.0,
           "head_in": 90.0}]
    model = _build(fp3d, _doc([_roof()], openings=op))
    assert model.stats["openings"] == 1
    v = _wall_verts(model)
    e = v[np.abs(v[:, 1]) <= EXT_T / 2 + 1e-6]
    assert e[:, 2].max() <= EAVES_H + SLOPE * EXT_T / 2 + 1e-6
    # the under-sill piece survives: a flat top at z=30, the opening's width
    sill = e[np.isclose(e[:, 2], 30.0)]
    assert len(sill) >= 4 and sill[:, 0].max() - sill[:, 0].min() == pytest.approx(30.0)
    # and nothing of the header: no vertex between the head and the wall top
    assert not np.any((e[:, 2] > 90.0 - 1e-6) & (e[:, 2] <= WALL_H + 1e-6))


def test_a_roof_on_another_level_does_not_cap_this_levels_walls(fp3d):
    doc = _doc([dict(_roof(), level="L2")])
    doc["levels"].append({"id": "L2", "elevation_in": 120.0, "height_in": 96.0})
    v = _wall_verts(_build(fp3d, doc, levels=["L1"]))
    assert v[:, 2].max() == pytest.approx(WALL_H)


# --------------------------------------------------------------------------
# two roofs: each caps its OWN territory
# --------------------------------------------------------------------------
def test_under_a_cross_gable_the_wing_caps_the_wall_not_the_mains_phantom(fp3d):
    """tests/test_roof_intersection.py's L (eaves lowered to 80): a wall
    at plan y=350 runs across the wing's body (x 140..260), outside the
    main's footprint (y 100..300). Under the wing it is capped by the
    WING's surface -- 130 at the ridge x=200, 80 at its eaves x=140/260 --
    and beyond the wing, where no roof is, it stands full height."""
    main = _roof(eaves_h=80.0, ridge_h=150.0, ridge=((0, 200), (400, 200)),
                 span=(100, 100), rid="main")
    wing = _roof(eaves_h=80.0, ridge_h=130.0, ridge=((200, 250), (200, 500)),
                 span=(60, 60), rid="wing")
    doc = {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": WALL_H}],
           "vertices": [{"id": "a", "x": 100, "y": 350}, {"id": "b", "x": 300, "y": 350}],
           "walls": [{"id": "w1", "level": "L1", "v1": "a", "v2": "b", "type": "interior"}],
           "rooms": [], "furnishings": [], "roofs": [main, wing]}
    v = _wall_verts(_build(fp3d, doc))
    wing_slope = (130.0 - 80.0) / 60.0
    for x, y, z in v:
        if 140.0 + 1e-6 < x < 260.0 - 1e-6:
            assert z <= 130.0 - wing_slope * abs(x - 200.0) + 1e-6, (x, y, z)
    # at the wing's eave line the capped piece ends at the eaves height and
    # the uncovered piece beyond it stands at the wall top: a real step,
    # because nothing roofs the wall there
    at_eave = v[np.isclose(v[:, 0], 140.0)]
    assert np.any(np.isclose(at_eave[:, 2], 80.0)), "no capped vertex at the eave"
    assert np.any(np.isclose(at_eave[:, 2], WALL_H)), "no full-height vertex beyond it"
    outside = v[v[:, 0] < 140.0 - 4.0]
    assert outside[:, 2].max() == pytest.approx(WALL_H)


def test_the_capped_wall_is_a_closed_solid_with_outward_tops(fp3d):
    """Every capped piece is a `_prism_slab` on a flat base: its top ring is
    on the surface, its bottom ring at the piece's base, and the top cap's
    normal points up -- so the walls still light like walls."""
    model = _build(fp3d, _doc([_roof()]))
    mesh = next(m for m in model.meshes if m.name == "walls:exterior")
    v, f = mesh.verts, mesh.faces
    ups = 0
    for a, b, c in f:
        n = np.cross(v[b] - v[a], v[c] - v[a])
        if abs(n[2]) > 1e-9 and v[a][2] > 1.0 and v[b][2] > 1.0 and v[c][2] > 1.0:
            assert n[2] > 0, "a top face wound downward"
            ups += 1
    assert ups >= 4, "no top faces found -- vacuous"
    assert math.isfinite(v[:, 2].max())


# --------------------------------------------------------------------------
# his own fixture: the three-ridge plan
# --------------------------------------------------------------------------
def test_on_the_three_ridge_fixture_no_wall_rises_above_the_roof_owning_its_ground(fp3d):
    """Every wall vertex under some roof's territory sits on or under THAT
    roof's surface -- the territories being the same `compute_roof_clips`
    result the roofs themselves are built from. Positive control first:
    built without roofs, the same walls do stand above the roof surfaces."""
    import json
    RC = fp3d.ROOFCLIP
    assert RC is not None
    doc = json.loads((ROOT / "fixtures" / "threeRidgeFloorplan.json").read_text())
    geoms = [RC.RoofGeom.from_record(rf) for rf in doc["roofs"]]
    per = RC.compute_roof_clips(geoms)
    terr = [(g, list(per[id(g)].region.cells) if per[id(g)].region is not None
             else [RC.footprint_polygon(g)]) for g in geoms]

    def owner_surface(x_w, y_w):
        pt = RC.Pt(x_w, -y_w)
        for g, cells in terr:
            if any(RC._contains(c, pt) for c in cells):
                return RC.surface_height(g, pt)
        return None

    def above(model):
        n = 0
        for x, y, z in _wall_verts(model):
            h = owner_surface(x, y)
            if h is not None and z > h + 1e-6:
                n += 1
        return n

    # the fixture's own walls (96in) never top its 96in eaves, so the
    # viewer's wall-height override (its own --wall-height) raises them to
    # 120in: through every slope, under all three territories at once
    control = fp3d.build_model(doc, furnishings=False, floors=False, roofs=False,
                               wall_height=120.0)
    assert above(control) > 0, "control: the unclipped walls never reach the roofs"
    clipped = fp3d.build_model(doc, furnishings=False, floors=False,
                               wall_height=120.0)
    assert above(clipped) == 0
    assert _wall_verts(clipped)[:, 2].max() == pytest.approx(120.0),         "some wall must still reach 120in where a ridge clears it"
