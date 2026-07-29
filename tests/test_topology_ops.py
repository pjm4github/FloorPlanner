"""P3.4 sub-commit (i): the planner/applier split, and the scene applier for
`merge_collinear`.

The point of the split is that ONE pure planner decides, and two thin appliers
mutate -- so these tests come in pairs wherever they can: the same decision,
checked once on a `Design` and once on the live scene. The scene half is the
new code; the `Design` half is the guard that the rebuild did not change what
the pure op means.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner import vertex
from floorplanner.design import topology
from floorplanner.design.bridge import design_from_scene
from floorplanner.design.model import Design
from floorplanner.walls import (
    apply_merge_plan_to_scene, graph_from_scene, merge_all,
    merge_collinear_scene, normalize_walls, plan_merge_collinear,
    split_wall_at, weld_scene,
)

pytestmark = pytest.mark.walls


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _design(verts, walls, level="L1"):
    """A minimal Design: verts is {id: (x, y)}, walls a list of wall dicts."""
    return Design.from_dict({
        "levels": [{"id": level, "name": "Level", "elevation_in": 0}],
        "vertices": [{"id": k, "level": level, "x": x, "y": y}
                     for k, (x, y) in verts.items()],
        "walls": [dict({"level": level, "type": "interior"}, **w)
                  for w in walls],
        "rooms": [], "furnishings": [], "groups": [],
    })


def _pos(d):
    return {v.id: (v.x, v.y) for v in d.vertices}


def _walls(scene, fp):
    return [w for w in scene.items()
            if isinstance(w, fp.WallItem) and not w.is_open]


def _add(scene, fp, x1, y1, x2, y2, wall_type="interior"):
    w = fp.WallItem(QPointF(x1, y1), QPointF(x2, y2), wall_type)
    scene.addItem(w)
    return w


def _door(fp, wall, s, code="3280"):
    op = fp.OpeningItem(wall, "door", code, s)
    wall.openings.append(op)
    wall.rebuild()
    return op


# --------------------------------------------------------------------------
# The pure planner: what it decides, on a Design
# --------------------------------------------------------------------------
def test_two_collinear_walls_at_a_degree_2_corner_plan_one_merge():
    d = _design({"a": (0, 0), "m": (100, 0), "b": (200, 0)},
                [{"id": "w1", "v1": "a", "v2": "m"},
                 {"id": "w2", "v1": "m", "v2": "b"}])
    plan = topology.plan_merge_collinear(topology.graph_from_design(d))
    assert len(plan) == 1
    assert plan[0].survivor == "w1" and plan[0].absorbed == ("w2",)
    assert plan[0].dropped_vertices == ("m",)      # the corner is consumed


def test_a_third_wall_at_the_corner_blocks_the_merge():
    # a real T-junction is load-bearing for the planar subdivision: the corner
    # has degree 3, so the run must NOT be merged through it
    d = _design({"a": (0, 0), "m": (100, 0), "b": (200, 0), "t": (100, 100)},
                [{"id": "w1", "v1": "a", "v2": "m"},
                 {"id": "w2", "v1": "m", "v2": "b"},
                 {"id": "w3", "v1": "m", "v2": "t"}])
    assert topology.plan_merge_collinear(topology.graph_from_design(d)) == []


def test_different_types_never_merge():
    d = _design({"a": (0, 0), "m": (100, 0), "b": (200, 0)},
                [{"id": "w1", "v1": "a", "v2": "m", "type": "interior"},
                 {"id": "w2", "v1": "m", "v2": "b", "type": "exterior"}])
    assert topology.plan_merge_collinear(topology.graph_from_design(d)) == []


def test_the_survivor_keeps_its_own_direction():
    # THE FIX FOUND BY SINGLE-SOURCING. The old merge_collinear wrote
    # `w1.v1, w1.v2 = far1, far2`, which REVERSES the survivor when the run
    # extends behind its v1 -- and it did not swap `left`/`right` to match, so
    # every side on that wall silently flipped. The survivor now keeps its own
    # direction, so left/right stay on the sides they were on.
    d = _design({"a": (0, 0), "m": (100, 0), "b": (200, 0)},
                [{"id": "w1", "v1": "m", "v2": "b", "left": "r1",
                  "right": "r2"},
                 {"id": "w2", "v1": "a", "v2": "m"}])
    merged = topology.merge_collinear(d)
    assert len(merged.walls) == 1
    w = merged.walls[0]
    pos = _pos(merged)
    assert pos[w.v1] == (0.0, 0.0) and pos[w.v2] == (200.0, 0.0)
    assert (w.left, w.right) == ("r1", "r2")


def test_merge_redistributes_an_opening_onto_the_merged_span():
    # merge_collinear used to REFUSE any wall carrying an opening. It now
    # redistributes: the door stays where it is in space, re-anchored to the
    # nearest end of the merged wall.
    d = _design({"a": (0, 0), "m": (100, 0), "b": (200, 0)},
                [{"id": "w1", "v1": "a", "v2": "m"},
                 {"id": "w2", "v1": "m", "v2": "b",
                  "openings": [{"id": "o1", "kind": "door", "code": "3280",
                                "anchor": {"from": "v1", "offset_in": 50.0}}]}])
    merged = topology.merge_collinear(d)
    assert len(merged.walls) == 1
    ops = merged.walls[0].openings
    assert len(ops) == 1
    # 50.0 -> 18.0 AT P3.6 (defect 24): `offset_in` is to the opening's NEAR
    # EDGE, so this test's old expectation was reading it as a centre distance
    # -- the same half-width the merge applier was dropping. The DOOR HAS NOT
    # MOVED: its centre is at x=166 before and after, which is now what the
    # test asserts, with the anchor value second.
    from floorplanner.design.bridge import _opening_s
    assert _opening_s(ops[0].anchor["from"], ops[0].anchor["offset_in"],
                      32.0, 200.0) == pytest.approx(166.0)
    assert ops[0].anchor == {"from": "v2", "offset_in": 18.0}


def test_merge_collinear_still_preserves_the_corpus_faces():
    # the delegation guard: the rebuilt op must still mean what P1.3's did
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    d = Design.from_dict(json.loads(
        (root / "examples" / "symmetricP1.json").read_text("utf-8")))
    d2 = topology.merge_collinear(d)
    assert len(d2.walls) <= len(d.walls)
    assert len(topology.trace_faces(d2)) == len(topology.trace_faces(d))


# --------------------------------------------------------------------------
# The scene applier: the same decisions, on live items
# --------------------------------------------------------------------------
def test_scene_merges_two_collinear_walls_end_to_end(fp, scene):
    _add(scene, fp, 0, 0, 100, 0)
    _add(scene, fp, 100, 0, 200, 0)
    assert merge_collinear_scene(scene) == 1
    walls = _walls(scene, fp)
    assert len(walls) == 1
    assert (walls[0].p1.x(), walls[0].p2.x()) == (0.0, 200.0)


def test_scene_leaves_a_real_t_junction_alone(fp, scene):
    _add(scene, fp, 0, 0, 100, 0)
    _add(scene, fp, 100, 0, 200, 0)
    _add(scene, fp, 100, 0, 100, 100)
    assert merge_collinear_scene(scene) == 0
    assert len(_walls(scene, fp)) == 3


def test_scene_merges_overlapping_duplicates_like_coalesce_did(fp, scene):
    # parity with tests/test_coalesce.py: two parallel walls 6" apart (within
    # the wall-snap grid) with overlapping spans are one wall
    _add(scene, fp, 0, 0, 120, 0)
    _add(scene, fp, 60, 6, 180, 6)
    merge_collinear_scene(scene)
    assert len(_walls(scene, fp)) == 1


def test_scene_does_not_merge_walls_off_the_grid(fp, scene):
    _add(scene, fp, 0, 0, 120, 0)
    _add(scene, fp, 0, 18, 120, 18)               # 18" apart, > the 6" grid
    assert merge_collinear_scene(scene) == 0
    assert len(_walls(scene, fp)) == 2


def test_scene_merge_is_idempotent(fp, scene):
    for i in range(5):                            # a chain of overlaps
        _add(scene, fp, i * 30, 0, i * 30 + 90, 0)
    merge_collinear_scene(scene)
    assert len(_walls(scene, fp)) == 1
    assert merge_collinear_scene(scene) == 0      # nothing left to do
    assert len(_walls(scene, fp)) == 1


def test_scene_merge_unions_the_rooms_the_walls_border(fp, scene, make_room):
    room = make_room(scene, 0, 0, 120, 120, "Den")
    edge = next(w for w in room.walls if w.length() > 1)
    free = _add(scene, fp, edge.p1.x(), edge.p1.y(), edge.p2.x(), edge.p2.y(),
                edge.wall_type)
    merge_collinear_scene(scene)
    survivor = next(w for w in _walls(scene, fp)
                    if w.length() > 1 and room in w.rooms
                    and abs(w.p1.y() - edge.p1.y()) < 1)
    assert room in survivor.rooms and survivor in room.walls
    assert free not in _walls(scene, fp) or free is survivor


# --------------------------------------------------------------------------
# Defect 9 -- merge dedups openings. Live-editing shaped, per the task text:
# planc1's three stacked doors were cleaned at IMPORT; this guards the path
# that created them, which is the one still open.
# --------------------------------------------------------------------------
def _two_walls_one_door_each(fp, scene):
    a = _add(scene, fp, 0, 0, 120, 0)
    b = _add(scene, fp, 0, 0, 120, 0)
    _door(fp, a, 60.0)
    _door(fp, b, 60.0)
    return a, b


def test_defect_9_merge_dedups_identical_openings(fp, scene):
    _two_walls_one_door_each(fp, scene)
    merge_collinear_scene(scene)
    walls = _walls(scene, fp)
    assert len(walls) == 1
    assert len(walls[0].openings) == 1            # not two stacked doors


# The companion to the test above ran the SAME input through
# `_coalesce_all_impl` and asserted it produced two stacked doors, so the
# closure was legible rather than merely claimed. It was deleted at P3.4 (iv)
# with the op it exercised: once the defect's implementation is gone there is
# no old behaviour left to exhibit, and a test that constructs one would be
# asserting against a museum piece. It did its job at (i) and (ii) -- the
# measured evidence is in the Progress log, which is where a claim about code
# that no longer exists belongs.


def test_merge_keeps_openings_that_are_genuinely_different(fp, scene):
    a = _add(scene, fp, 0, 0, 240, 0)
    b = _add(scene, fp, 0, 0, 240, 0)
    _door(fp, a, 60.0)
    _door(fp, b, 180.0)                           # far apart: both are real
    merge_collinear_scene(scene)
    walls = _walls(scene, fp)
    assert len(walls) == 1
    assert sorted(round(op.s) for op in walls[0].openings) == [60, 180]


def test_merged_opening_stays_where_it_was_in_space(fp, scene):
    _add(scene, fp, 0, 0, 100, 0)
    b = _add(scene, fp, 100, 0, 200, 0)
    _door(fp, b, 50.0)                            # absolute (150, 0)
    merge_collinear_scene(scene)
    wall = _walls(scene, fp)[0]
    assert len(wall.openings) == 1
    p = wall.point_at(wall.openings[0].s)
    assert abs(p.x() - 150.0) < 0.01 and abs(p.y()) < 0.01


# --------------------------------------------------------------------------
# The properties that made the planner/applier split worth the trouble
# --------------------------------------------------------------------------
def test_an_end_to_end_merge_adopts_the_corner_instead_of_splitting(fp, scene):
    # coalesce assigned p1/p2, which is SPLIT-ON-WRITE: the corner came apart
    # and was rebuilt from coordinates. The merge re-points the end AT the
    # corner's vertex, so an exact merge causes no split at all.
    _add(scene, fp, 0, 0, 100, 0)
    _add(scene, fp, 100, 0, 200, 0)
    before = vertex.split_count()
    merge_collinear_scene(scene)
    assert vertex.split_count() == before


def test_the_applier_touches_only_the_items_the_delta_names(fp, scene):
    _add(scene, fp, 0, 0, 100, 0)
    _add(scene, fp, 100, 0, 200, 0)
    bystander = _add(scene, fp, 0, 400, 100, 400)
    v1, v2 = bystander.end_vertex("p1"), bystander.end_vertex("p2")
    merge_collinear_scene(scene)
    assert bystander.scene() is scene
    assert bystander.end_vertex("p1") is v1 and bystander.end_vertex("p2") is v2


def test_the_plan_is_a_delta_the_scene_can_be_asked_for_first(fp, scene):
    # planning does not mutate: a caller can look at the delta and decline
    _add(scene, fp, 0, 0, 100, 0)
    _add(scene, fp, 100, 0, 200, 0)
    plan = plan_merge_collinear(graph_from_scene(scene), perp_tol=6.0)
    assert len(plan) == 1 and len(_walls(scene, fp)) == 2
    apply_merge_plan_to_scene(scene, plan)
    assert len(_walls(scene, fp)) == 1


def test_floors_are_planned_apart(fp, scene):
    a = _add(scene, fp, 0, 0, 100, 0)
    b = _add(scene, fp, 100, 0, 200, 0)
    b.floor = "upper"
    assert merge_collinear_scene(scene) == 0
    assert len(_walls(scene, fp)) == 2
    assert a.floor != b.floor


# --------------------------------------------------------------------------
# split_edge scene-side -- the other half of the op pair
# --------------------------------------------------------------------------
def test_scene_split_cuts_the_wall_and_shares_the_new_corner(fp, scene):
    a = _add(scene, fp, 0, 0, 240, 0)
    seg = split_wall_at(scene, a, QPointF(120, 0))
    assert seg is not None
    assert (a.p1.x(), a.p2.x()) == (0.0, 120.0)
    assert (seg.p1.x(), seg.p2.x()) == (120.0, 240.0)
    assert a.end_vertex("p2") is seg.end_vertex("p1"), (
        "the split corner must be ONE vertex, not two at the same place")


def test_scene_split_costs_no_split_on_writes(fp, scene):
    # vertex-native: both new ends are handed over with set_end_vertex, so the
    # op never assigns a coordinate and never mints an anonymous corner
    a = _add(scene, fp, 0, 0, 240, 0)
    before = vertex.split_count()
    split_wall_at(scene, a, QPointF(120, 0))
    assert vertex.split_count() == before


def test_scene_split_keeps_the_far_ends_existing_sharing(fp, scene):
    a = _add(scene, fp, 0, 0, 240, 0)
    b = _add(scene, fp, 240, 0, 240, 120)
    b.set_end_vertex("p1", a.end_vertex("p2"))    # weld the far corner by hand
    seg = split_wall_at(scene, a, QPointF(120, 0))
    assert seg.end_vertex("p2") is b.end_vertex("p1"), "the far corner broke"


def test_scene_split_moves_openings_onto_the_segment_that_holds_them(fp, scene):
    a = _add(scene, fp, 0, 0, 240, 0)
    _door(fp, a, 40.0)                            # first segment
    _door(fp, a, 200.0)                           # second segment
    seg = split_wall_at(scene, a, QPointF(120, 0))
    assert [round(op.s) for op in a.openings] == [40]
    assert [round(op.s) for op in seg.openings] == [80]      # 200 - 120
    assert round(seg.point_at(seg.openings[0].s).x()) == 200  # same place


def test_scene_split_through_a_doorway_happens_and_is_reported(fp, scene):
    """FLIPPED AT R2c -- old: `assert split_wall_at(...) is None`, the gesture
    declining. WHY THE ASSERTION MOVED: it is defect 17's lesson. A gesture that
    silently does nothing is the worst of the three options, and we were keeping
    a second case of it on purpose. The two policies on one delta are gone: the
    primitive and the scene op now do the same thing and differ only in where
    each surfaces its report."""
    a = _add(scene, fp, 0, 0, 240, 0)
    _door(fp, a, 120.0)                           # 32" wide: spans 104..136
    report = []
    seg = split_wall_at(scene, a, QPointF(120, 0), report=report)
    assert seg is not None, "the gesture silently did nothing"
    assert len(_walls(scene, fp)) == 2
    assert len(report) == 1 and "no longer fits" in report[0]


def test_scene_split_declines_at_an_endpoint(fp, scene):
    a = _add(scene, fp, 0, 0, 240, 0)
    assert split_wall_at(scene, a, QPointF(0, 0)) is None
    assert split_wall_at(scene, a, QPointF(240, 0)) is None
    assert len(_walls(scene, fp)) == 1


def test_split_then_merge_returns_the_wall_it_started_with(fp, scene):
    # the two ops are inverses, and running them back to back on a scene is the
    # cheapest possible statement of that
    a = _add(scene, fp, 0, 0, 240, 0)
    _door(fp, a, 40.0)
    split_wall_at(scene, a, QPointF(120, 0))
    assert len(_walls(scene, fp)) == 2
    merge_collinear_scene(scene)
    walls = _walls(scene, fp)
    assert len(walls) == 1
    assert (walls[0].p1.x(), walls[0].p2.x()) == (0.0, 240.0)
    assert [round(op.s) for op in walls[0].openings] == [40]


# --------------------------------------------------------------------------
# The weld family, and the command that outlives its implementation
# --------------------------------------------------------------------------
def test_the_weld_snap_still_closes_a_gap(fp, scene):
    # the GEOMETRY half, preserved verbatim from weld_all/join_endpoints: a
    # free end within JOIN_TOL (9") of another wall's end moves onto it. It is
    # the only way a drawn or pixel-extracted plan closes its junctions.
    a = _add(scene, fp, 0, 0, 120, 0)
    b = _add(scene, fp, 124, 0, 124, 120)         # 4" short of a's end
    moved, _shared = weld_scene(scene)
    assert moved >= 1
    assert b.p1.x() == pytest.approx(a.p2.x(), abs=0.6)


def test_welding_makes_a_corner_topology_not_just_coordinates(fp, scene):
    # the half weld_all never had. Asserted with `is`, never `==`: equal
    # coordinates are exactly what weld_all already produced.
    a = _add(scene, fp, 0, 0, 120, 0)
    b = _add(scene, fp, 124, 0, 124, 120)
    assert a.end_vertex("p2") is not b.end_vertex("p1")
    weld_scene(scene)
    assert a.end_vertex("p2") is b.end_vertex("p1")


def test_weld_scene_does_not_split_a_body_landing(fp, scene):
    # THE RULE, pinned: splitting edits a wall the user did not touch, so it
    # belongs to the explicit pass and nowhere else. Without this, migrating
    # imageio's weld_all would silently turn a 5-wall extracted plan into 7.
    _add(scene, fp, 0, 0, 240, 0)
    _add(scene, fp, 120, 0, 120, 120)
    weld_scene(scene)
    assert len(_walls(scene, fp)) == 2


def test_normalize_walls_does_split_a_body_landing(fp, scene):
    _add(scene, fp, 0, 0, 240, 0)
    _add(scene, fp, 120, 0, 120, 120)
    merged, _moved, _shared, split = normalize_walls(scene)
    assert (merged, split) == (0, 1)
    assert len(_walls(scene, fp)) == 3


def test_normalize_walls_merges_and_welds_in_one_pass(fp, scene):
    _add(scene, fp, 0, 0, 120, 0)                 # two collinear runs...
    _add(scene, fp, 120, 0, 240, 0)
    _add(scene, fp, 244, 0, 244, 120)             # ...and a 4" gap to close
    merged, moved, _shared, _split = normalize_walls(scene)
    assert merged == 1 and moved >= 1
    assert len(_walls(scene, fp)) == 2


def test_normalize_walls_ignores_the_auto_coalesce_switch(fp, scene):
    # "Coalesce all walls now" is the user asking explicitly, so the automatic
    # gate does not apply -- as the old command called the _impl directly
    fp.SETTINGS["auto_coalesce"] = False
    try:
        _add(scene, fp, 0, 0, 120, 0)
        _add(scene, fp, 60, 0, 180, 0)
        assert merge_all(scene) == 0              # the gated entry declines
        assert normalize_walls(scene)[0] == 1     # the explicit one does not
        assert len(_walls(scene, fp)) == 1
    finally:
        fp.SETTINGS["auto_coalesce"] = True


def test_the_menu_command_still_tidies_the_plan(fp, win):
    # the command outlives its implementation: same menu item, new machinery
    for p, q in (((0, 0), (120, 0)), ((120, 0), (240, 0)),
                 ((120, 0), (120, 120))):
        win.scene.addItem(fp.WallItem(QPointF(*p), QPointF(*q), "interior"))
    fp.rebuild_all_walls(win.scene)
    win.coalesce_all_now()
    walls = [w for w in win.scene.items()
             if isinstance(w, fp.WallItem) and not w.is_open]
    # the T-junction is load-bearing, so the run does NOT merge through it;
    # what the pass achieves is that the corner is now one shared vertex
    assert len(walls) == 3
    at_tee = [w for w in walls
              if any(abs(getattr(w, a).x() - 120) < 0.1
                     and abs(getattr(w, a).y()) < 0.1 for a in ("p1", "p2"))]
    assert len(at_tee) == 3
    verts = {id(w.end_vertex(a)) for w in at_tee for a in ("p1", "p2")
             if abs(getattr(w, a).x() - 120) < 0.1
             and abs(getattr(w, a).y()) < 0.1}
    assert len(verts) == 1, "the welded corner is still three coordinates"


# --------------------------------------------------------------------------
# The query helpers -- migrated to vertex adjacency, or pinned against it
# --------------------------------------------------------------------------
def test_joined_at_is_a_degree_query_that_matches_the_search_it_replaced(
        fp, scene):
    """`_joined_at` was a 0.6" coordinate search; it is now a degree lookup on
    the corner fold. Its own un-indexed fallback still runs the old search, so
    the two are compared directly -- the replacement carries its own oracle."""
    _add(scene, fp, 0, 0, 120, 0)
    _add(scene, fp, 120, 0, 120, 120)             # joined at (120, 0)
    _add(scene, fp, 300, 0, 420, 0)               # joined to nothing
    _add(scene, fp, 0, 300, 120, 300)
    _add(scene, fp, 120, 300.4, 120, 420)         # 0.4" apart: still ONE corner
    index = fp.walls._WallIndex(scene)
    for w in _walls(scene, fp):
        for attr in ("p1", "p2"):
            assert w._joined_at(attr, index) == w._joined_at(attr), (
                f"indexed and un-indexed disagree on {attr}")
    by_p1 = {(w.p1.x(), w.p1.y()): w for w in _walls(scene, fp)}
    assert by_p1[(0.0, 0.0)]._joined_at("p2", index) is True    # the corner
    assert by_p1[(0.0, 0.0)]._joined_at("p1", index) is False   # free end
    assert by_p1[(300.0, 0.0)]._joined_at("p1", index) is False
    assert by_p1[(0.0, 300.0)]._joined_at("p2", index) is True  # 0.4" apart


def test_coincidence_agrees_with_the_planners_own_predicate(fp, scene):
    """THE DRIFT GATE for the one predicate that is stated twice.

    `coincident_walls` stays a hand-rolled scan because it sits on the app's
    hottest path (`WallItem.rebuild`, once per wall per pass) and routing it
    through the planner would allocate a view per candidate. The planner's
    `_same_line` + `_spans_overlap` are transcriptions of it. Two statements of
    one rule is exactly the F2 disease this task exists to avoid, so they are
    policed instead of merged -- the same move `--verify-design` makes for the
    two appliers."""
    pairs = [((0, 0, 120, 0), (60, 0, 180, 0)),        # overlapping duplicates
             ((0, 0, 120, 0), (60, 6, 180, 6)),        # 6" off the line
             ((0, 0, 120, 0), (0, 18, 120, 18)),       # 18" off: not coincident
             ((0, 0, 120, 0), (120, 0, 240, 0)),       # abutting, no overlap
             ((0, 0, 120, 0), (0, 0, 0, 120)),         # perpendicular
             ((0, 0, 120, 120), (60, 60, 180, 180))]   # diagonal pair
    for i, (pa, pb) in enumerate(pairs):
        sc = type(scene)()
        a = _add(sc, fp, *pa)
        b = _add(sc, fp, *pb)
        got = b in fp.coincident_walls(sc, a, perp_tol=6.0)
        view = graph_from_scene(sc)
        va = next(v for v in view.walls if v.key is a)
        vb = next(v for v in view.walls if v.key is b)
        want = (topology._same_line(va, vb, view.pos, 6.0, topology.ANGLE_TOL)
                and topology._spans_overlap(va, vb, view.pos))
        assert got == want, f"pair {i} {pa} / {pb}: scan {got}, planner {want}"
        sc.clear()


def test_the_scene_applier_leaves_the_design_applier_nothing_to_do(fp, scene):
    # THE DRIFT GATE IN MINIATURE. If the two appliers disagreed, the pure op
    # would still find a merge in the document the scene walk produces.
    _add(scene, fp, 0, 0, 100, 0)
    _add(scene, fp, 100, 0, 200, 0)
    _add(scene, fp, 200, 0, 200, 100)
    merge_collinear_scene(scene)
    d = design_from_scene(scene)
    assert topology.plan_merge_collinear(topology.graph_from_design(d)) == []
