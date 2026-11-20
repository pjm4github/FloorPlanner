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


# -- 0352 phase 3: a FURNISHING dormer is built as a roof on its host ---------
def _furnishing_doc(over_host=True):
    """A host roof + a dormer FURNISHING (not a roof record). The dormer's
    anchor (pos) sits on the host's south slope; `fp3d` resolves the host by the
    anchor and folds the dormer in as a roof record (`_dormer_roof_records`)."""
    host = {"id": "rf1", "level": "L1", "ridge": [[0, 100], [400, 100]],
            "eaves_h_in": 96.0, "ridge_h_in": 150.0, "overhang_in": [12, 12],
            "span_in": [100, 100], "gable": [True, True]}
    state = {"form": "gable", "span_left_in": 30.0, "span_right_in": 30.0,
             "symmetric": True, "pitch_12": 6.0, "eaves_h_in": 110.0,
             "depth_in": 40.0, "eave_overhang_left_in": 0.0,
             "eave_overhang_right_in": 0.0, "face_overhang_in": 0.0}
    return {"levels": [{"id": "L1", "elevation_in": 0.0, "height_in": 96.0}],
            "vertices": [], "walls": [], "rooms": [],
            "roofs": [host] if over_host else [],
            "furnishings": [{"kind": "dormer", "level": "L1", "pos": [200, 130],
                             "rotation": 0.0, "state": state}]}


def test_a_furnishing_dormer_is_built_as_a_roof_on_its_host(fp3d):
    model = fp3d.build_model(_furnishing_doc(True), furnishings=False, floors=False)
    assert any("dormer furnishing" in n for n in model.notes), model.notes
    roof = next((m for m in model.meshes if m.name == "roofs"), None)
    cheeks = [m for m in model.meshes if m.name.startswith("walls:")]
    assert roof is not None and len(roof.verts) > 16, "host + the dormer's planes"
    assert cheeks, "the dormer's cheeks stand on the host"


def test_a_furnishing_dormer_over_no_roof_contributes_no_mesh(fp3d):
    model = fp3d.build_model(_furnishing_doc(False), furnishings=False, floors=False)
    assert not any("dormer furnishing" in n for n in model.notes)
    assert not any(m.name == "roofs" for m in model.meshes)


def test_a_cantilevered_dormer_floor_is_closed_underneath(fp3d):
    """DORMER_CONTROL_SPEC.md sec 8.4 (Patrick, 2026-11-19): a furnishing dormer
    pushed PAST the host eave no longer hangs open below -- its face drops to the
    attic floor (base(level)=0 here) and a floor slab closes the overhang
    underneath. P3.2b's open hang at the eave line is superseded."""
    import numpy as np
    doc = _furnishing_doc(True)
    doc["furnishings"][0]["state"]["depth_in"] = 90.0   # face at y=230, past eave y=200
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    walls = next((m for m in model.meshes if m.name.startswith("walls:")), None)
    assert walls is not None
    ys = -walls.verts[:, 1]
    assert np.any(ys > 205.0), "the cantilevered face is generated past the host eave"
    # the face now reaches DOWN to the attic floor (0), not just the eave line (110+)
    past = walls.verts[ys > 205.0]
    assert past[:, 2].min() < 5.0, "the cantilever face drops to the attic floor"
    # and the floor is closed underneath
    floor = next((m for m in model.meshes if m.name == "dormer_floor"), None)
    assert floor is not None and len(floor.verts) > 0, "a floor slab closes the overhang"
    assert -floor.verts[:, 1].min() > 200.0 or (-floor.verts[:, 1]).max() > 200.0, \
        "the floor sits under the overhang, past the host eave"
    assert floor.verts[:, 2].max() < 5.0, "the floor is at the attic level"


def test_a_balcony_dormer_cuts_the_host_and_lays_a_deck(fp3d):
    """P3.2a (Patrick, 2026-11-19): a balcony dormer cuts the host roof in front
    of its face and lays a flat deck at the dormer level's floor (the attic
    floor) -- the user's railing walls stand on it."""
    doc = _furnishing_doc(True)
    doc["furnishings"][0]["state"]["face_mode"] = "balcony"
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    deck = next((m for m in model.meshes if m.name == "balcony"), None)
    assert deck is not None and len(deck.verts) > 0, "a balcony deck is laid"
    assert deck.verts[:, 2].max() == pytest.approx(0.0, abs=1.1), "flat at the floor"
    plain = fp3d.build_model(_furnishing_doc(True), furnishings=False, floors=False)
    roof_b = next(m for m in model.meshes if m.name == "roofs")
    roof_p = next(m for m in plain.meshes if m.name == "roofs")
    assert len(roof_b.verts) < len(roof_p.verts), "the host roof is cut for the terrace"


def test_a_shed_balcony_cuts_the_host_in_front_of_the_face_not_sideways(fp3d):
    """Patrick, 2026-11-19: a SHED balcony was cutting the host 90 deg off --
    sideways across the width instead of downhill in front of the face. The
    shed's roof record carries its ridge ACROSS the width, so `_balcony_terraces`
    has to read the forward (toward-face) axis as the high edge's normal. Here
    the dormer anchor is at plan y=130, its face ~y=170; the cut terrace and its
    deck must lie IN FRONT of the face (plan y > 170, toward the south eave at
    y=200), never beside it."""
    doc = _furnishing_doc(True)
    st = doc["furnishings"][0]["state"]
    st["form"] = "shed"
    st["pitch_12"] = 4.0            # shallower than the host (0.54) so it meets
    st["eaves_h_in"] = 112.0
    st["face_mode"] = "balcony"
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    deck = next((m for m in model.meshes if m.name == "balcony"), None)
    assert deck is not None and len(deck.verts) > 0, "a shed balcony lays a deck"
    plan_y = -deck.verts[:, 1]     # world (x, -y, z) -> plan y
    assert plan_y.min() > 170.0 - 1.0, "the terrace is in FRONT of the face, not sideways"
    assert plan_y.max() <= 200.0 + 12.0 + 1e-6, "no deeper than the host south eave"


def test_a_front_wall_bounds_the_balcony_deck_short_of_the_eave(fp3d):
    """DORMER_CONTROL_SPEC.md sec 8.1 (Patrick, 2026-11-19): the balcony deck and
    the host cut stop at the wall the user draws in front of the face, not out at
    the eave. Face ~y=170, host south eave y=200; a railing wall at y=185 across
    the width must pull the deck's forward edge back to ~185."""
    doc = _furnishing_doc(True)
    doc["furnishings"][0]["state"]["face_mode"] = "balcony"
    doc["vertices"] = [{"id": "ra", "x": 152, "y": 185}, {"id": "rb", "x": 248, "y": 185}]
    doc["walls"] = [{"id": "rail", "level": "L1", "v1": "ra", "v2": "rb", "type": "railing"}]
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    deck = next((m for m in model.meshes if m.name == "balcony"), None)
    assert deck is not None and len(deck.verts) > 0, "a deck is still laid"
    plan_y = -deck.verts[:, 1]
    assert plan_y.max() <= 185.0 + 6.0, "the deck stops at the front wall, not the eave"
    # the control: no wall -> the deck runs out toward the eave (y ~ 200)
    plain = dict(doc, walls=[], vertices=[])
    pdeck = next(m for m in fp3d.build_model(plain, furnishings=False, floors=False).meshes
                 if m.name == "balcony")
    assert (-pdeck.verts[:, 1]).max() > 190.0, "unbounded, the deck reaches the eave"


def _shed_balcony_doc_with_wall(wtype, face_mode="balcony"):
    """A shed balcony on a host, ceiling raised to 120 so a wall standing in the
    terrace (an INTERIOR one, which the dormer never generates) would poke above
    the low host roofline near the eave unless the balcony frees it."""
    doc = _furnishing_doc(True)
    doc["levels"][0]["height_in"] = 120.0
    st = doc["furnishings"][0]["state"]
    st.update(form="shed", pitch_12=4.0, eaves_h_in=112.0, face_mode=face_mode)
    doc["vertices"] = [{"id": "ra", "x": 152, "y": 190}, {"id": "rb", "x": 248, "y": 190}]
    doc["walls"] = [{"id": "bw", "level": "L1", "v1": "ra", "v2": "rb", "type": wtype}]
    return doc


def test_a_balcony_wall_rises_free_of_the_cut_host_roof(fp3d):
    """DORMER_CONTROL_SPEC.md sec 8.2 (Patrick, 2026-11-19): a wall in the
    balcony rises to the attic ceiling, not capped by the cut-away host roof.
    An interior wall at plan y=190 (host roofline ~101 there) reaches the 120"
    ceiling as a balcony; as a plain set-back dormer the host roof caps it."""
    free = fp3d.build_model(_shed_balcony_doc_with_wall("interior"),
                            furnishings=False, floors=False)
    w = next(m for m in free.meshes if m.name == "walls:interior")
    assert w.verts[:, 2].max() == pytest.approx(120.0, abs=2.0), "rises to the ceiling"
    capped = fp3d.build_model(_shed_balcony_doc_with_wall("interior", "setback"),
                              furnishings=False, floors=False)
    w2 = next(m for m in capped.meshes if m.name == "walls:interior")
    assert w2.verts[:, 2].max() < 110.0, "no balcony -> the host roof caps it"


def test_a_balcony_railing_stands_at_railing_height(fp3d):
    """sec 8.3: a railing-type wall in the balcony rises only to railing height
    (36"), not the ceiling."""
    model = fp3d.build_model(_shed_balcony_doc_with_wall("railing"),
                             furnishings=False, floors=False)
    rail = next(m for m in model.meshes if m.name == "walls:railing")
    assert rail.verts[:, 2].max() == pytest.approx(fp3d.WALL_H["railing"], abs=1.0)


def test_a_cantilevered_balcony_deck_reaches_past_the_host_to_the_wall(fp3d):
    """DORMER_CONTROL_SPEC.md sec 8.5 (Patrick, 2026-11-19): when the railing is
    PAST the host eave the balcony is cantilevered -- its deck must still reach
    the wall, over the overhang where there is no host roof to cut. Face ~y=170,
    host south eave y=200, railing y=230: the deck must reach ~230."""
    doc = _furnishing_doc(True)
    doc["furnishings"][0]["state"]["face_mode"] = "balcony"
    doc["vertices"] = [{"id": "ra", "x": 152, "y": 230}, {"id": "rb", "x": 248, "y": 230}]
    doc["walls"] = [{"id": "rail", "level": "L1", "v1": "ra", "v2": "rb", "type": "railing"}]
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    deck = next((m for m in model.meshes if m.name == "balcony"), None)
    assert deck is not None and len(deck.verts) > 0
    plan_y = -deck.verts[:, 1]
    assert plan_y.max() > 225.0, "the deck reaches out past the host eave to the wall"
    assert deck.verts[:, 2].max() < 5.0, "the deck lies flat at the attic floor"
