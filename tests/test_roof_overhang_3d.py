"""THE LOWER ROOF RUNS UNDER THE OVERHANG, in 3D (Patrick, 2026-10-11, on
his `short-angle-roof.json`; read back at 0239-report.md, ordered at
0240-report.md: *"the wall loop test is right"*).

The second-floor roof `rf4` has its ridge from x=108 to x=366 while the
second floor's walls stand at x=120 and x=354: a 12-inch gable overhang
at each end, over the two first-floor short roofs. The plan's clip hides
`rf1` under `rf4` from x=108 on, and the 3D mesh used to be the visible
region and nothing else -- so `rf1` stopped at x=108 with a vertical cut
face, 12 inches short of the gable wall it should meet, and `rf4`'s open
gable-end slab stood over a gap. Now a clipped roof also meshes the
cells of its OWN footprint the clip hid wherever their centroid lies
outside every wall loop of the covering roof's level -- under an
overhang -- cut at the seam where its surface would rise above the
cover's. `fp3d.py` is loaded by path, as `test_viewer_model.py` does.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.viewer

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SHORT_ANGLE = FIXTURES / "short-angle-roof.json"
SHORT_ANGLE_R2 = FIXTURES / "short-angle-roofR2.json"     # his, with a dormer
SHORT_ANGLE_R3 = FIXTURES / "short-angle-roofR3.json"     # his, the dormer set back


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_overhang_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _doc(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _roof_verts(fp3d, doc):
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    assert not model.notes, model.notes
    mesh = next(m for m in model.meshes if m.name == "roofs")
    return {(round(float(x), 4), round(float(y), 4), round(float(z), 4))
            for x, y, z in mesh.verts.tolist()}


def _without_the_rule(fp3d, monkeypatch, doc):
    """The roof mesh as it was built before the rule: the overhang mesher
    returning nothing."""
    monkeypatch.setattr(fp3d, "_hidden_overhang_pieces", lambda *a, **k: [])
    return _roof_verts(fp3d, doc)


# ---------------------------------------------------------------------------
# the wall loops -- the test his word named
# ---------------------------------------------------------------------------
def test_the_second_floor_walls_are_one_box_and_the_overhang_is_outside_it(fp3d):
    doc = _doc("short-angle-roof.json")
    vx = {v["id"]: v for v in doc["vertices"]}
    loops = fp3d._wall_loops(doc["walls"], doc["rooms"], vx, "L2")
    assert len(loops) == 1
    assert sorted(loops[0]) == [(120.0, 120.0), (120.0, 360.0), (354.0, 120.0), (354.0, 360.0)]
    # the hidden strip's centroid, x=114: outside; the storey itself: inside
    assert not fp3d._pip((114.0, 240.0), loops[0])
    assert fp3d._pip((200.0, 240.0), loops[0])
    assert not fp3d._pip((360.0, 240.0), loops[0])
    # the first floor's 24 walls enclose the whole house, x=114 included
    first = fp3d._wall_loops(doc["walls"], doc["rooms"], vx, "L1")
    assert len(first) == 7
    assert any(fp3d._pip((114.0, 240.0), loop) for loop in first)


def test_a_dangling_wall_encloses_nothing_and_a_room_outline_counts(fp3d):
    vx = {"a": {"id": "a", "x": 0.0, "y": 0.0}, "b": {"id": "b", "x": 100.0, "y": 0.0},
          "c": {"id": "c", "x": 100.0, "y": 50.0}, "d": {"id": "d", "x": 0.0, "y": 50.0},
          "e": {"id": "e", "x": 150.0, "y": 25.0}}
    box = [{"id": "w1", "level": "L", "v1": "a", "v2": "b"},
           {"id": "w2", "level": "L", "v1": "b", "v2": "c"},
           {"id": "w3", "level": "L", "v1": "c", "v2": "d"},
           {"id": "w4", "level": "L", "v1": "d", "v2": "a"}]
    spur = [{"id": "w5", "level": "L", "v1": "c", "v2": "e"}]
    # an open U is no loop; the box is one; the spur off it adds none
    assert fp3d._wall_loops(box[:3], [], vx, "L") == []
    assert len(fp3d._wall_loops(box, [], vx, "L")) == 1
    loops = fp3d._wall_loops(box + spur, [], vx, "L")
    assert len(loops) == 1
    assert fp3d._pip((50.0, 25.0), loops[0]) and not fp3d._pip((125.0, 25.0), loops[0])
    # a room outline is a loop in its own right, walls or no walls
    room = [{"id": "r", "level": "L", "outline": [{"v": "a"}, {"v": "b"}, {"v": "c"}]}]
    assert len(fp3d._wall_loops([], room, vx, "L")) == 1
    # another level's walls are not this level's
    assert fp3d._wall_loops(box, [], vx, "M") == []


# ---------------------------------------------------------------------------
# his design: rf1 reaches its gable wall; rf2 the mirror; rf4 still above
# ---------------------------------------------------------------------------
def test_the_short_roofs_run_under_the_overhang_to_the_gable_walls(fp3d, monkeypatch):
    doc = _doc("short-angle-roof.json")
    after = _roof_verts(fp3d, doc)
    before = _without_the_rule(fp3d, monkeypatch, doc)
    T = fp3d.ROOF_T
    # rf1's ridge end at the gable wall, x=120, at its own ridge height
    # 216, and its eaves corners there at 96 -- none of it was built before
    for p in [(120.0, -240.0, 216.0), (120.0, -240.0, 216.0 - T),
              (120.0, -120.0, 96.0), (120.0, -360.0, 96.0)]:
        assert p in after and p not in before, p
    # rf2, the mirror at x=354
    for p in [(354.0, -240.0, 216.0), (354.0, -120.0, 96.0), (354.0, -360.0, 96.0)]:
        assert p in after and p not in before, p
    # nothing of rf1 east of its wall, nothing of rf2 west of its: between
    # the gable walls every roof vertex is rf4's own surface or its slab
    # underside (276 - |y - 240| in absolute height), never a lower roof
    inside = [(x, y, z) for x, y, z in after if 120.0 + 1e-6 < x < 354.0 - 1e-6]
    assert inside
    for x, y, z in inside:
        top = 276.0 - abs(-y - 240.0)
        assert top - T - 1e-6 <= z <= top + 1e-6, (x, y, z)
    # rf4's overhang slab is still there above rf1: its ridge end at
    # x=108 and its cells' corners at x=120, at rf4's own heights
    for p in [(108.0, -240.0, 276.0), (120.0, -240.0, 276.0), (108.0, -120.0, 156.0)]:
        assert p in after and p in before, p
    # the rule added, and removed nothing
    assert before <= after
    assert len(after - before) == 30


def test_the_added_pieces_are_the_hidden_strips_of_the_own_footprints(fp3d):
    """Straight from the mesher: rf1's two cells x 108..120 either side of
    its ridge, each under rf4 and outside the second floor's box; rf2's
    strip x 354..366 likewise, except where rf3 (first floor, inside the
    house) covers it; rf3's strip under rf4 at the same place; nothing
    for rf4, which nothing covers."""
    doc = _doc("short-angle-roof.json")
    RC = fp3d.ROOFCLIP
    vx = {v["id"]: v for v in doc["vertices"]}
    elev = {lv["id"]: float(lv["elevation_in"]) for lv in doc["levels"]}
    every = []
    for rec in doc["roofs"]:
        g = RC.RoofGeom.from_record(rec)
        every.append((rec["id"], rec["level"], g, RC.Lifted(g, elev[rec["level"]])))
    per = RC.compute_roof_clips([lf for _, _, _, lf in every])
    terr = [(lf, list(per[id(lf)].region.cells), False, lid) for _, lid, _, lf in every]
    loops = {lid: fp3d._wall_loops(doc["walls"], doc["rooms"], vx, lid) for lid in elev}
    got = {}
    for rid, _lid, g, lf in every:
        clip = per[id(lf)]
        got[rid] = fp3d._hidden_overhang_pieces(g, lf, clip, terr, loops.__getitem__, RC)
    xs = lambda pcs: sorted({round(p.x(), 3) for pc in pcs for p in pc})  # noqa: E731
    assert xs(got["rf1"]) == [108.0, 120.0]
    assert sum(RC._area(pc) for pc in got["rf1"]) == pytest.approx(12.0 * 240.0)
    assert xs(got["rf2"]) == [354.0, 366.0]
    # rf2's strip is short of the full 12 x 240 by the cell rf3 draws,
    # which lies inside the first floor's walls (x 240..420, y 120..360)
    assert 0 < sum(RC._area(pc) for pc in got["rf2"]) < 12.0 * 240.0
    assert xs(got["rf3"]) == [354.0, 366.0]
    assert got["rf4"] == []
    # every added piece lies at or below the roof covering it
    for rid, _lid, _g, lf in every:
        for pc in got[rid]:
            c = RC._centroid(pc)
            cover = [o for o, cells, _, _ in terr if o is not lf
                     and any(RC._contains(cell, c) for cell in cells)]
            assert cover and all(RC.surface_height(o, v) >= RC.surface_height(lf, v) - RC.EPS
                                 for o in cover for v in pc), rid


# ---------------------------------------------------------------------------
# the seam: to it, not through it
# ---------------------------------------------------------------------------
def test_a_hidden_cell_the_lower_roof_would_rise_through_is_cut_at_the_seam(fp3d):
    """A steep lower roof (96/196 over a 100in half-span) wholly hidden
    under a shallow upper one (absolute 106/136 over the same span,
    ridges collinear): the lower rises above the upper within 60/0.7 =
    85.7in of the ridge, so only the two eaves strips beyond that --
    2 x 14.29 x 100 sq in -- are built, cut exactly where the surfaces
    meet. Nothing of the cover's level is enclosed, so the loop test
    passes everywhere; the seam alone decides."""
    RC = fp3d.ROOFCLIP
    lower = RC.RoofGeom.from_record({"ridge": [[0.0, 100.0], [100.0, 100.0]], "span_in": [100.0, 100.0],
                                     "overhang_in": [0.0, 0.0], "eaves_h_in": 96.0, "ridge_h_in": 196.0,
                                     "gable": [True, True]})
    upper = RC.RoofGeom.from_record({"ridge": [[-50.0, 100.0], [200.0, 100.0]], "span_in": [100.0, 100.0],
                                     "overhang_in": [0.0, 0.0], "eaves_h_in": 10.0, "ridge_h_in": 40.0,
                                     "gable": [True, True]})
    lower_abs, upper_abs = RC.Lifted(lower, 0.0), RC.Lifted(upper, 96.0)
    clip = RC.RoofClip(RC.ClipRegion([]), [], [], (0.0, 0.0))      # everything hidden
    terr = [(upper_abs, [RC.footprint_polygon(upper_abs)], False, "L2")]
    far = [[(1000.0, 1000.0), (1001.0, 1000.0), (1001.0, 1001.0)]]
    pieces = fp3d._hidden_overhang_pieces(lower, lower_abs, clip, terr, lambda lid: far, RC)
    assert pieces
    cut = 100.0 - 60.0 / 0.7
    assert sum(RC._area(pc) for pc in pieces) == pytest.approx(2.0 * cut * 100.0, abs=1e-3)
    for pc in pieces:
        for v in pc:
            assert RC.surface_height(upper_abs, v) >= RC.surface_height(lower_abs, v) - 1e-6
            assert abs(v.y() - 100.0) >= cut - 1e-6
    # the same cells with the lower roof under the upper everywhere (a
    # low lower roof) are built whole: the cut is a cut, not a filter
    low = RC.RoofGeom.from_record({"ridge": [[0.0, 100.0], [100.0, 100.0]], "span_in": [100.0, 100.0],
                                   "overhang_in": [0.0, 0.0], "eaves_h_in": 60.0, "ridge_h_in": 100.0,
                                   "gable": [True, True]})
    whole = fp3d._hidden_overhang_pieces(low, RC.Lifted(low, 0.0), clip, terr, lambda lid: far, RC)
    assert sum(RC._area(pc) for pc in whole) == pytest.approx(200.0 * 100.0, abs=1e-3)


def test_a_level_with_no_walls_states_no_overhang_and_a_dormer_is_not_one(fp3d):
    RC = fp3d.ROOFCLIP
    low = RC.RoofGeom.from_record({"ridge": [[0.0, 100.0], [100.0, 100.0]], "span_in": [100.0, 100.0],
                                   "overhang_in": [0.0, 0.0], "eaves_h_in": 60.0, "ridge_h_in": 100.0,
                                   "gable": [True, True]})
    upper = RC.RoofGeom.from_record({"ridge": [[-50.0, 100.0], [200.0, 100.0]], "span_in": [100.0, 100.0],
                                     "overhang_in": [0.0, 0.0], "eaves_h_in": 10.0, "ridge_h_in": 40.0,
                                     "gable": [True, True]})
    clip = RC.RoofClip(RC.ClipRegion([]), [], [], (0.0, 0.0))
    cover = RC.Lifted(upper, 96.0)
    assert fp3d._hidden_overhang_pieces(low, RC.Lifted(low, 0.0), clip,
                                        [(cover, [RC.footprint_polygon(cover)], False, "L2")],
                                        lambda lid: [], RC) == []
    assert fp3d._hidden_overhang_pieces(low, RC.Lifted(low, 0.0), clip,
                                        [(cover, [RC.footprint_polygon(cover)], True, "L2")],
                                        lambda lid: [[(1000.0, 1000.0), (1001.0, 1000.0), (1001.0, 1001.0)]],
                                        RC) == []


# ---------------------------------------------------------------------------
# the other roof fixtures: what the rule does and does not touch, measured
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["single-floor-90-roof-gable-end-check.json",
                                  "dormer-gable-check.json",
                                  "roofs-r3-orbit-check.json",
                                  "r6c-two-level-tool-check.json"])
def test_fixtures_with_nothing_hidden_outside_the_walls_build_unchanged(fp3d, monkeypatch, name):
    doc = _doc(name)
    assert _roof_verts(fp3d, doc) == _without_the_rule(fp3d, monkeypatch, doc)


@pytest.mark.parametrize("name, added", [("threeRidgeFloorplan.json", 18),
                                         ("threeRidgeShortRidgeFloorplan.json", 6)])
def test_the_three_ridge_fixtures_gain_only_rf1s_eave_strip_under_rf3_at_the_notch(
        fp3d, monkeypatch, name, added):
    """Measured, not assumed (0240-report.md sec1 item 4 expected these
    unchanged): at the re-entrant corner between rooms B and D -- outside
    the house's walls -- rf1's eaves strip runs under rf3's, and the rule
    builds it: slivers within 14in of the eaves height, every vertex at
    or under rf3's surface, inside rf1's own footprint (y <= 642), and
    nothing removed. Visible from under rf3's soffit only."""
    doc = _doc(name)
    after = _roof_verts(fp3d, doc)
    before = _without_the_rule(fp3d, monkeypatch, doc)
    assert before <= after
    new = after - before
    assert len(new) == added
    RC = fp3d.ROOFCLIP
    rf = {r["id"]: RC.RoofGeom.from_record(r) for r in doc["roofs"]}
    for x, y, z in new:
        p = RC.Pt(x, -y)
        assert 540.0 <= x <= 645.0 and 550.0 <= -y <= 642.0 + 1e-6, (x, y, z)
        assert z <= 96.0 + 14.0 + 1e-6
        assert z <= RC.surface_height(rf["rf3"], p) + 1e-6, (x, y, z)
        assert RC._contains(RC.footprint_polygon(rf["rf1"]), p, tol=1e-3) \
            or RC._contains(RC.footprint_polygon(rf["rf3"]), p, tol=1e-3)



# ---------------------------------------------------------------------------
# nothing of roof material hangs from a roof's edge: the riser on any
# footprint edge of the higher roof is gone (Patrick, 2026-10-11, on
# short-angle-roofR2.json, twice -- the gable ends, then the dormer's cheeks:
# "They should not have any spill over on the edge of the roof")
# ---------------------------------------------------------------------------
def _composed(fp3d, doc):
    RC = fp3d.ROOFCLIP
    elev = {lv["id"]: float(lv["elevation_in"]) for lv in doc["levels"]}
    every = {}
    for rec in doc["roofs"]:
        g = RC.RoofGeom.from_record(rec)
        every[rec["id"]] = RC.Lifted(g, elev[rec["level"]])
    per = RC.compute_roof_clips(list(every.values()))
    return every, per


def _risers(fp3d, doc):
    every, per = _composed(fp3d, doc)
    return fp3d._cross_roof_risers([(lf, per[id(lf)]) for lf in every.values()], fp3d.ROOFCLIP)


def _seg_hits(mesh, a, b):
    """Segment a->b against every triangle of `mesh` (Moller-Trumbore)."""
    import numpy as np
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
    t_ = a - v0
    u = np.einsum("ij,ij->i", t_, pv) * inv
    q = np.cross(t_, e1)
    v = np.einsum("j,ij->i", d, q) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t >= 0) & (t <= 1)
    return int(hit.sum())


def test_the_r2_fixture_is_the_base_case_plus_a_dormer():
    base = _doc("short-angle-roof.json")
    r2 = _doc("short-angle-roofR2.json")
    assert [r["id"] for r in r2["roofs"]] == ["rf1", "rf2", "rf3", "rf4", "rf5"]
    for rid in ("rf1", "rf2", "rf4"):
        a = next(r for r in base["roofs"] if r["id"] == rid)
        b = next(r for r in r2["roofs"] if r["id"] == rid)
        assert (a["ridge"], a["eaves_h_in"], a["ridge_h_in"]) == (b["ridge"], b["eaves_h_in"], b["ridge_h_in"]), rid
    dormer = r2["roofs"][4]
    assert dormer["host"] == "rf4" and dormer["level"] == "L2"
    assert dormer["ridge"] == [[234.0, 366.0], [234.0, 252.0]] and dormer["span_in"] == [48.0, 48.0]
    # the dormer's front stands 6in past rf4's south eaves line (y=360)
    assert dormer["ridge"][0][1] == 366.0


def test_the_footprint_edge_test_knows_an_edge_from_the_inside(fp3d):
    RC = fp3d.ROOFCLIP
    g = RC.RoofGeom.from_record({"ridge": [[108.0, 240.0], [366.0, 240.0]], "span_in": [120.0, 120.0],
                                 "overhang_in": [0.0, 0.0], "eaves_h_in": 60.0, "ridge_h_in": 180.0,
                                 "gable": [True, True]})
    P = RC.Pt
    assert fp3d._on_footprint_edge(g, P(108.0, 120.0), P(108.0, 240.0), RC)       # the west rake
    assert fp3d._on_footprint_edge(g, P(366.0, 300.0), P(366.0, 360.0), RC)       # the east rake
    assert fp3d._on_footprint_edge(g, P(108.0, 120.0), P(200.0, 120.0), RC)       # the eave
    assert not fp3d._on_footprint_edge(g, P(120.0, 120.0), P(120.0, 240.0), RC)   # inside
    assert not fp3d._on_footprint_edge(g, P(108.0, 120.0), P(109.0, 240.0), RC)   # skew
    assert not fp3d._on_footprint_edge(g, P(108.0, 240.0), P(108.0, 400.0), RC)   # past the corner
    hip = RC.RoofGeom.from_record({"ridge": [[108.0, 240.0], [366.0, 240.0]], "span_in": [120.0, 120.0],
                                   "overhang_in": [0.0, 0.0], "eaves_h_in": 60.0, "ridge_h_in": 180.0,
                                   "gable": [False, True]})
    assert not fp3d._on_footprint_edge(hip, P(108.0, 120.0), P(108.0, 240.0), RC)  # under the hip
    assert fp3d._on_footprint_edge(hip, P(-12.0, 120.0), P(-12.0, 240.0), RC)      # its eave line


@pytest.mark.parametrize("name", ["short-angle-roof.json", "short-angle-roofR2.json"])
def test_no_riser_hangs_from_an_edge_of_the_higher_roof(fp3d, name):
    """Before: 13 risers on the base case, every one on the gable-end line
    of the roof standing higher there -- rf4's rakes at x=108 and x=366
    hanging roof material down to the short roofs, rf2's at x=426 and
    rf3's over the junction -- and on R2 two more on the dormer's eaves
    lines, its cheeks hanging to rf4. After: none on either."""
    doc = _doc(name)
    every, per = _composed(fp3d, doc)
    risers = fp3d._cross_roof_risers([(lf, per[id(lf)]) for lf in every.values()], fp3d.ROOFCLIP)
    assert risers == []
    # the positive control: the boundaries ARE there and mismatched -- the
    # detector with the edge rule off finds what it used to
    RC = fp3d.ROOFCLIP
    orig = fp3d._on_footprint_edge
    try:
        fp3d._on_footprint_edge = lambda *a, **k: False
        before = fp3d._cross_roof_risers([(lf, per[id(lf)]) for lf in every.values()], RC)
    finally:
        fp3d._on_footprint_edge = orig
    # 13 on the base case; on R2 15 segments of the same boundaries before
    # 0260's coarser arrangement, 12 since (fewer, longer pieces -- the
    # boundaries themselves are what the loop below checks, one by one)
    assert len(before) == (13 if name == "short-angle-roof.json" else 12)
    for (px, py), (qx, qy), *_heights in before:
        p, q = RC.Pt(px, py), RC.Pt(qx, qy)
        assert any(fp3d._on_footprint_edge(lf, p, q, RC) for lf in every.values()), (px, py, qx, qy)


@pytest.mark.parametrize("name", ["short-angle-roof.json", "short-angle-roofR2.json"])
def test_nothing_of_roof_hangs_below_the_upper_rakes_in_3d(fp3d, name):
    """The receipt in the mesh: rays through the plane of rf4's west rake
    (x=108) and east rake (x=366), inside the gap between the lower roof
    and rf4's underside, hit no roof triangle. Before, each hit the riser."""
    model = fp3d.build_model(_doc(name), furnishings=False, floors=False)
    roof = next(m for m in model.meshes if m.name == "roofs")
    # west rake at the ridge: rf1 at 216, rf4's underside at 272 -> z=244;
    # halfway down the slope (plan y=180): rf1 at 156, rf4 at 212 -> 184
    for x, y, z in [(108.0, 240.0, 244.0), (108.0, 180.0, 184.0), (108.0, 300.0, 184.0),
                    (366.0, 240.0, 244.0), (366.0, 300.0, 184.0)]:
        assert _seg_hits(roof, (x - 3.0, -y, z), (x + 3.0, -y, z)) == 0, (x, y, z)
    # the control: the same ray through rf4's own slab at the rake (its
    # top at 276 at the ridge, the slab 4in thick) does hit it
    assert _seg_hits(roof, (105.0, -240.0, 274.0), (111.0, -240.0, 274.0)) > 0


def test_on_r2_the_short_roofs_still_reach_their_gable_walls_and_the_cheeks_are_open(fp3d):
    doc = _doc("short-angle-roofR2.json")
    after = _roof_verts(fp3d, doc)
    for p in [(120.0, -240.0, 216.0), (120.0, -120.0, 96.0), (354.0, -240.0, 216.0), (354.0, -360.0, 96.0)]:
        assert p in after, p
    model = fp3d.build_model(doc, furnishings=False, floors=False)
    roof = next(m for m in model.meshes if m.name == "roofs")
    # the dormer's cheek planes x=186 and 282 between rf4's surface and the
    # dormer's eaves (216) at plan y=330 (rf4 at 186 -> z=200 is in the
    # gap): nothing of roof there -- no spill over the dormer's edge --
    # but WALL: the generated cheeks, projected up from rf4 to the dormer
    assert _seg_hits(roof, (183.0, -330.0, 200.0), (189.0, -330.0, 200.0)) == 0
    assert _seg_hits(roof, (279.0, -330.0, 200.0), (285.0, -330.0, 200.0)) == 0
    walls = next(m for m in model.meshes if m.name == "walls:exterior")
    assert _seg_hits(walls, (183.0, -330.0, 200.0), (189.0, -330.0, 200.0)) > 0
    assert _seg_hits(walls, (279.0, -330.0, 200.0), (285.0, -330.0, 200.0)) > 0
    # the cheeks stop where rf4 reaches the dormer's eaves (y=300) and do
    # not stand past rf4's own eave (y=360), though the dormer runs to 366
    # (the house walls w25 at y=120 and w28 at y=360 are split at x=186
    # too, by the dormer's cells, and w28 climbs into the dormer there:
    # the band y 250..356 between them is the cheek's alone)
    w = walls.verts
    cheek = w[(abs(w[:, 0] - 186.0) < 1e-3) & (-w[:, 1] > 250.0) & (-w[:, 1] < 356.0)]
    ys = -cheek[:, 1]
    assert cheek.size and 299.0 < ys.min() < 301.0 and ys.max() >= 354.0, (ys.min(), ys.max())
    assert cheek[:, 2].max() == pytest.approx(216.0 - 0.5) and cheek[:, 2].min() > 150.0
    # the control: the dormer's own slab is there (its ridge 264 at x=234)
    assert _seg_hits(roof, (234.0, -330.0, 250.0), (234.0, -330.0, 270.0)) > 0


@pytest.mark.parametrize("name", ["short-angle-roof.json", "short-angle-roofR2.json"])
def test_the_eaves_wall_under_the_overhang_keeps_the_profile_it_has_beside_it(fp3d, name):
    """His "strange step where the overhang sits": the first floor's north
    eaves wall w1 (plan y=120) runs under rf4's gable overhang from x=108
    to 120. Its pieces there were capped by rf4 (156in up -- a full
    96in box) while west of 108 they are capped by rf1's eave (the outer
    half under the eave line, the roof surface continued past it). Now
    rf1's hidden strip is rf1's territory and the LOWEST roof over a
    piece owns it, so the wall keeps one profile across x=108: the same
    set of top heights either side of it, and nothing at x in 108..120
    stands above what stands at x=100."""
    model = fp3d.build_model(_doc(name), furnishings=False, floors=False)
    v = next(m for m in model.meshes if m.name == "walls:exterior").verts
    # w1 is split at x=108 (rf1's visible cell ends there) and both pieces
    # end on that line, so the distinct heights AT x=108 are one profile
    # when the two pieces agree and two when they step: the base and the
    # three cap heights under rf1's eave, nothing at the full 96
    at108 = v[(abs(v[:, 1] + 120.0) < 4.0) & (abs(v[:, 0] - 108.0) < 1e-3)]
    heights = {round(float(z), 1) for z in at108[:, 2]}
    assert len(heights) == 4 and 0.0 in heights, sorted(heights)
    assert 85.0 < max(heights) < 96.0, sorted(heights)
    # and the piece under the overhang ends at the gable wall, x=120, with
    # the same profile (the second floor's own walls start at z=96 there)
    at120 = v[(abs(v[:, 1] + 120.0) < 4.0) & (abs(v[:, 0] - 120.0) < 1e-3) & (v[:, 2] < 96.0 - 1e-6)]
    assert {round(float(z), 1) for z in at120[:, 2]} == heights


# ---------------------------------------------------------------------------
# the dormer's face climbs from the roof when the dormer is set back
# (Patrick, 2026-10-11, short-angle-roofR3.json)
# ---------------------------------------------------------------------------
def test_r3_is_r2_with_the_dormer_set_back_onto_the_roof():
    r2, r3 = _doc("short-angle-roofR2.json"), _doc("short-angle-roofR3.json")
    assert r2["walls"] == r3["walls"] and r2["vertices"] == r3["vertices"]
    d2 = next(r for r in r2["roofs"] if r["id"] == "rf5")
    d3 = next(r for r in r3["roofs"] if r["id"] == "rf5")
    assert d2["ridge"][0] == [234.0, 366.0] and d3["ridge"][0] == [234.0, 336.0]
    assert {k: v for k, v in d2.items() if k != "ridge"} == {k: v for k, v in d3.items() if k != "ridge"}
    assert [r for r in r2["roofs"] if r["id"] != "rf5"] == [r for r in r3["roofs"] if r["id"] != "rf5"]


def test_a_set_back_dormers_face_is_generated_on_the_roof_and_a_face_past_the_eave_is_not(fp3d):
    """R3: the face at y=336 stands on rf4 (its surface there 180in; the
    dormer's rake 264 at the ridge, 216 at the sides), so a wall is
    generated across it, x 186..282, t inward (y 330..336), from an inch
    into rf4 up to half an inch under the rake -- rays through the face
    plane inside the gap hit wall, not roof: the hole closed. R2: the
    face at y=366 stands past rf4's eave (y=360); nothing is generated
    there, and w28 beneath it climbs into the dormer instead."""
    t = fp3d.WALL_T.get("exterior", 6.0)
    model = fp3d.build_model(_doc("short-angle-roofR3.json"), furnishings=False, floors=False)
    walls = next(m for m in model.meshes if m.name == "walls:exterior")
    roof = next(m for m in model.meshes if m.name == "roofs")
    for x, z in [(234.0, 220.0), (234.0, 250.0), (210.0, 200.0), (260.0, 200.0)]:
        assert _seg_hits(walls, (x, -340.0, z), (x, -329.0, z)) > 0, (x, z)
        assert _seg_hits(roof, (x, -340.0, z), (x, -329.0, z)) == 0, (x, z)
    w = walls.verts
    # (the gable wall w26 at x=120 is split on the face line too -- the
    # dormer's footprint edges are in the clip's cut set -- so the band
    # x 150..320 is the face's alone)
    face = w[(abs(-w[:, 1] - 336.0) < 1e-3) & (w[:, 2] > 150.0) & (w[:, 0] > 150.0) & (w[:, 0] < 320.0)]
    assert face[:, 0].min() == pytest.approx(186.0) and face[:, 0].max() == pytest.approx(282.0)
    assert face[:, 2].max() == pytest.approx(264.0 - 0.5)
    assert {round(float(y), 3) for y in -w[(abs(w[:, 0] - 234.0) < 1e-3) & (w[:, 2] > 250.0)][:, 1]} == {336.0, 336.0 - t}
    # R2: nothing generated on the face line; w28 climbs there
    model2 = fp3d.build_model(_doc("short-angle-roofR2.json"), furnishings=False, floors=False)
    walls2 = next(m for m in model2.meshes if m.name == "walls:exterior")
    w2 = walls2.verts
    assert not len(w2[(abs(-w2[:, 1] - 366.0) < 1e-3) & (w2[:, 2] > 150.0)
                      & (w2[:, 0] > 150.0) & (w2[:, 0] < 320.0)])
    assert _seg_hits(walls2, (234.0, -364.0, 240.0), (234.0, -356.0, 240.0)) > 0   # w28, climbed

