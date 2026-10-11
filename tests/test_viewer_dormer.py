"""R5b in 3D, as corrected by Patrick's look at the first dormer
(2026-09-24): *"the walls of the dormer are being drawn down from the
dormer. It should show only the roof line and intersect with the walls
under it."* So a dormer builds no walls of its own; the house walls under
its territory CLIMB into its roof -- `fp3d._wall_under_roofs` caps a
pier or header under a dormer at the dormer's plane whether that is
below or above the wall's own top -- and the roof meshes are unchanged
by the `host` field. Qt-free, fp3d loaded by path.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
MEET_Y = 100.0 + (150.0 - 136.0) / 0.54
DORMER_SLOPE = (136.0 - 116.0) / 30.0


def _load_fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_dormer_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fp3d():
    return _load_fp3d()


def _doc(with_host=True, walls=()):
    dormer = {"id": "rf2", "level": "L1", "ridge": [[200, 190], [200, MEET_Y]],
              "eaves_h_in": 116.0, "ridge_h_in": 136.0, "overhang_in": [0, 0],
              "span_in": [30, 30], "gable": [True, True], "marker_end": 0}
    if with_host:
        dormer["host"] = "rf1"
    return {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}],
            "vertices": [{"id": "a", "x": 100, "y": 170}, {"id": "b", "x": 300, "y": 170}],
            "walls": list(walls), "rooms": [], "furnishings": [],
            "roofs": [{"id": "rf1", "level": "L1", "ridge": [[0, 100], [400, 100]],
                       "eaves_h_in": 96.0, "ridge_h_in": 150.0, "overhang_in": [12, 12],
                       "span_in": [100, 100], "gable": [True, True]}, dormer]}


WALL = {"id": "w1", "level": "L1", "v1": "a", "v2": "b", "type": "interior"}


def _wall_verts(model):
    parts = [m.verts for m in model.meshes if m.name.startswith("walls:")]
    return np.vstack(parts) if parts else np.zeros((0, 3))


def test_a_dormer_builds_its_cheeks_on_the_host_roof_and_nothing_down_to_the_floor(fp3d):
    """0194 deleted the dormer's own walls, which hung DOWN from the dormer
    to the floor (his word then). On 2026-10-11, the cheek risers gone,
    his word: *"the dormer sides should be generated so that they are
    projected up to the dormer."* So the only walls a dormer builds are
    its two cheeks (`_dormer_cheeks`), exterior wall material standing on
    the HOST's surface along the dormer's wall lines x=170 and x=230 and
    rising to half an inch under its eaves (116in), where the host lies
    below them -- here from the face (y=190, host 101.4) back to y=163,
    where the host reaches 116 -- and nowhere near the floor."""
    model = fp3d.build_model(_doc(), furnishings=False, floors=False)
    assert not model.notes, model.notes
    assert [m.name for m in model.meshes if m.name.startswith("walls:")] == ["walls:exterior"]
    v = _wall_verts(model)
    assert len(v) > 0
    t = fp3d.WALL_T.get("exterior", 6.0)
    ys = -v[:, 1]
    # the cheeks: on the wall lines, from the face back to where the host
    # reaches the eaves; the face (`_dormer_face`, 0245): across the
    # width at y=190 and t inward, up to the rake
    cheeks = v[(ys < 190.0 - t - 1e-6)]
    xs = {round(float(x), 3) for x in cheeks[:, 0]}
    assert xs == {170.0, 170.0 + t, 230.0 - t, 230.0}, xs
    assert cheeks[:, 2].max() == pytest.approx(116.0 - 0.5)
    assert 162.0 < (-cheeks[:, 1]).min() < 164.0
    face = v[(abs(ys - 190.0) < 1e-6) | (abs(ys - (190.0 - t)) < 1e-6)]
    assert face[:, 0].min() == pytest.approx(170.0) and face[:, 0].max() == pytest.approx(230.0)
    assert face[:, 2].max() == pytest.approx(136.0 - 0.5)          # the ridge, less the half inch
    assert v[:, 2].min() > 96.0, "a piece reached below the host's eaves"
    assert ys.max() == pytest.approx(190.0)
    # every base vertex stands an inch into the host's slab at its own point
    for x, y, z in v:
        on_rake = abs(z - (136.0 - DORMER_SLOPE * abs(x - 200.0) - 0.5)) < 1e-6
        if not on_rake and z < 116.0 - 0.5 - 1e-6:
            assert z == pytest.approx(150.0 - 0.54 * abs(-y - 100.0) - 1.0, abs=0.3), (x, y, z)


def test_a_wall_under_a_dormer_climbs_into_its_roof(fp3d):
    """An interior wall at plan y=170 crossing the dormer (x 170..230):
    under the dormer its top is the dormer plane less the cap drop --
    131.5in at the ridge line, above the level's 96in walls; outside the
    dormer, where the host plane clears 96in, the wall keeps its top."""
    model = fp3d.build_model(_doc(walls=[WALL]), furnishings=False, floors=False)
    assert not model.notes, model.notes
    # the interior mesh alone: the dormer's own cheeks are exterior wall
    v = next(m for m in model.meshes if m.name == "walls:interior").verts
    assert len(v) > 8, "the wall was split under the dormer"
    c = fp3d.WALL_CAP_BELOW_ROOF_IN
    under = v[(v[:, 0] > 170.0 + 1e-6) & (v[:, 0] < 230.0 - 1e-6) & (v[:, 2] > 1.0)]
    assert len(under) >= 2
    for x, y, z in under:
        assert z == pytest.approx(136.0 - DORMER_SLOPE * abs(x - 200.0) - c, abs=1e-6), (x, y, z)
    assert v[:, 2].max() == pytest.approx(136.0 - c)
    outside = v[v[:, 0] < 170.0 - 1e-6]
    assert outside[:, 2].max() == pytest.approx(96.0)
    # the control: the same wall with no dormer never rises above its top
    plain = fp3d.build_model(_doc(with_host=False, walls=[WALL]), furnishings=False,
                             floors=False)
    assert _wall_verts(plain)[:, 2].max() <= 96.0 + 1e-6


def test_the_wall_under_a_sill_does_not_climb(fp3d):
    wall = dict(WALL, openings=[{"id": "o1", "kind": "window", "code": "3050",
                                 "anchor": {"from": "start", "offset_in": 100},
                                 "sill_in": 30.0, "head_in": 80.0}])
    model = fp3d.build_model(_doc(walls=[wall]), furnishings=False, floors=False)
    v = next(m for m in model.meshes if m.name == "walls:interior").verts   # not the dormer's own
    sill = v[np.isclose(v[:, 2], 30.0)]
    assert len(sill) >= 4, "the under-sill piece keeps its own flat top"
    assert v[:, 2].max() == pytest.approx(136.0 - fp3d.WALL_CAP_BELOW_ROOF_IN)


def test_the_roof_meshes_are_unchanged_by_the_host_field(fp3d):
    with_host = fp3d.build_model(_doc(True), furnishings=False, floors=False)
    without = fp3d.build_model(_doc(False), furnishings=False, floors=False)
    a = next(m for m in with_host.meshes if m.name == "roofs")
    b = next(m for m in without.meshes if m.name == "roofs")
    assert np.array_equal(a.verts, b.verts) and np.array_equal(a.faces, b.faces)


# --------------------------------------------------------------------------
# 0195-ruling.md sec3: what closes the dormer below its eaves -- named and probed
# --------------------------------------------------------------------------
def _seg_hits(verts, faces, a, b):
    """Segment a->b against every triangle (Moller-Trumbore): the hit count."""
    a = np.array(a, float)
    b = np.array(b, float)
    d = b - a
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    t_ = a - v0
    u = np.einsum("ij,ij->i", t_, p) * inv
    q = np.cross(t_, e1)
    v = np.einsum("j,ij->i", d, q) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t >= 0) & (t <= 1)
    return int(hit.sum())


# rays CROSSING each plane inside the gap between the host's surface and the
# dormer's eaves (world = (x, -y, z)): the left eaves plane x=170 and the
# right x=230 at plan y=180 (host 106.8, eaves 116 -> z=111); the front y=190
# at x=200 and x=225 (host 101.4, eaves 116 -> z=108), along y across it
_GAP_RAYS = {
    "left eaves plane": ((165, -180, 111), (175, -180, 111)),
    "right eaves plane": ((225, -180, 111), (235, -180, 111)),
    "front, at the ridge": ((200, -195, 108), (200, -185, 108)),
    "front, near a corner": ((225, -195, 108), (225, -185, 108)),
}


def _roof_hits(fp3d):
    model = fp3d.build_model(_doc(), furnishings=False, floors=False)
    roof = next(m for m in model.meshes if m.name == "roofs")
    return {name: _seg_hits(roof.verts, roof.faces, a, b)
            for name, (a, b) in _GAP_RAYS.items()}


def test_nothing_of_roof_closes_the_dormer_below_its_eaves(fp3d, monkeypatch):
    """0195-ruling.md sec3 asked what closes the dormer below its eaves and
    the answer, probed here until 2026-10-11, was R4f's cross-roof risers
    -- the double-sided quads drawn along every boundary where two roofs'
    territories meet at unequal height: the dormer's two eaves lines and
    its face, each a riser from the host's surface up to the dormer.

    NOW NOTHING DOES, by Patrick's word on his `short-angle-roofR2.json`
    3D view (2026-10-11): *"The brown roof material should not cover the
    gable ends"*, then, the dormer's cheeks circled, *"They should not
    have any spill over on the edge of the roof."* A riser on any
    footprint edge of the higher roof is a sheet of roof material
    hanging from that edge, and `_cross_roof_risers` no longer emits
    one: the face is a gable end, open; the cheeks are the dormer's
    eaves, open. What closes a dormer is what closes a gable: the walls
    beneath it, which climb into it
    (`test_a_wall_under_a_dormer_climbs_into_its_roof`). Probed: the
    rays through all three planes inside the gap hit NO ROOF, risers on
    or off; the control ray through the dormer's own slab hits. What
    closes the two eaves planes is WALL -- the generated cheeks
    (`_dormer_cheeks`, his word of the same day: *"the dormer sides should
    be generated so that they are projected up to the dormer"*) -- and
    what closes the face, which stands on the host here, is the generated
    face (`_dormer_face`): all four rays hit the walls mesh."""
    hits = _roof_hits(fp3d)
    assert all(n == 0 for n in hits.values()), hits
    monkeypatch.setattr(fp3d, "_cross_roof_risers", lambda *a, **k: [])
    assert all(n == 0 for n in _roof_hits(fp3d).values())
    model = fp3d.build_model(_doc(), furnishings=False, floors=False)
    roof = next(m for m in model.meshes if m.name == "roofs")
    assert _seg_hits(roof.verts, roof.faces, (200, -180, 120), (200, -180, 140)) > 0   # the dormer's ridge slab
    walls = next(m for m in model.meshes if m.name == "walls:exterior")
    wall_hits = {name: _seg_hits(walls.verts, walls.faces, a, b) for name, (a, b) in _GAP_RAYS.items()}
    assert wall_hits["left eaves plane"] > 0 and wall_hits["right eaves plane"] > 0, wall_hits
    # and the face too, since it stands on the host (`_dormer_face`, his
    # word of 2026-10-11 on the set-back dormer: "the dormer face needs
    # to climb up from the roof itself")
    assert wall_hits["front, at the ridge"] > 0 and wall_hits["front, near a corner"] > 0, wall_hits
