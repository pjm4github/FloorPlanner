"""P3.3 -- a wall move is a VERTEX move.

Two claims are under test here and they are different claims.

The first is about the DOCUMENT: in v5 a wall move edits exactly two vertices
and nothing else, and every room outline that references them follows for free.
That is the port of `tools/demo_move_wall.py`, and it is a statement about the
data model -- no scene, no Qt.

The second is about the EDITOR: dragging a wall's body now moves the vertices
under it rather than scanning for coincident coordinates and pushing each one by
hand. The observable difference is sharing. A neighbour follows because it is
the same corner, not because a loop remembered it -- and the split rule says
which neighbours may become the same corner in the first place.

Outlines were still produced by DETECTION when this file was written, so the
scene tests asserted the areas detection arrived at -- the honest thing to
assert while detection was the authority. P3.5 flipped that and then deleted
the detector, so `test_a_dragged_wall_resizes_the_rooms_it_borders` now asserts
the same numbers for a different reason. That test surviving the deletion
unchanged is P3.5's headline check (rider 1), and it is annotated as such below.
"""
import json
import pathlib

import pytest
from PyQt6.QtCore import QPointF, Qt

from floorplanner.design import validate as VD
from floorplanner.vertex import Vertex

pytestmark = pytest.mark.walls

EXAMPLES = pathlib.Path(__file__).resolve().parent.parent / "examples"
NOMOD = Qt.KeyboardModifier.NoModifier


# --------------------------------------------------------------------------
# the document claim -- tools/demo_move_wall.py, ported
# --------------------------------------------------------------------------
def _polygon_area_sf(doc, room):
    pos = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    pts = [pos[e["v"]] for e in room["outline"]]
    s = 0.0
    for i, (x1, y1) in enumerate(pts):
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2 / 144


def _shared_wall(doc, a, b, horizontal=True):
    """The unique axis-aligned wall with `a` on one side and `b` on the other.

    Picked by GEOMETRY AND ROOMS, never by id. The demo script named `w24`, but
    ids are canonical -- `design/canonical.py` renumbers them by geometry at
    serialization -- so the Gate 2 fixture regeneration (82 walls -> 80) moved
    every wall id in this file. A test pinned to an id would have failed for a
    renumbering rather than for a regression, which is the wrong signal."""
    pos = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    names = {r["id"]: r["name"] for r in doc["rooms"]}
    hits = []
    for w in doc["walls"]:
        if not (w.get("left") and w.get("right")):
            continue
        if {names[w["left"]], names[w["right"]]} != {a, b}:
            continue
        (x1, y1), (x2, y2) = pos[w["v1"]], pos[w["v2"]]
        if (abs(y1 - y2) < 1e-9) == horizontal and abs(x1 - x2) > 1e-9:
            hits.append(w)
        elif not horizontal and abs(x1 - x2) < 1e-9 and abs(y1 - y2) > 1e-9:
            hits.append(w)
    assert len(hits) == 1, f"expected one {a}|{b} wall, got {len(hits)}"
    return hits[0]


def test_moving_a_wall_edits_exactly_two_vertices():
    """The port of `tools/demo_move_wall.py`: move the Lounge / Front Porch
    party wall by +12" and exactly those two rooms resize, by equal and opposite
    17.5 sf, with the plan total unchanged and the document still valid.

    The demo's point, and the point of the whole phase: the ENTIRE operation is
    two numbers changing in `vertices`. Nothing walks the rooms, nothing
    re-derives an outline, nothing can drift -- because the outlines never held
    coordinates to drift from."""
    doc = json.loads((EXAMPLES / "symmetricP1.json").read_text("utf-8"))
    wall = _shared_wall(doc, "Lounge", "Front Porch", horizontal=True)
    moved = set((wall["v1"], wall["v2"]))

    before = {r["name"]: _polygon_area_sf(doc, r) for r in doc["rooms"]}
    for v in doc["vertices"]:
        if v["id"] in moved:
            v["y"] += 12.0                       # THE WHOLE OPERATION
    after = {r["name"]: _polygon_area_sf(doc, r) for r in doc["rooms"]}

    changed = {n: after[n] - before[n] for n in before
               if abs(after[n] - before[n]) > 0.001}
    assert set(changed) == {"Lounge", "Front Porch"}
    assert changed["Lounge"] == pytest.approx(17.5)
    assert changed["Front Porch"] == pytest.approx(-17.5)
    assert sum(after.values()) == pytest.approx(sum(before.values()))
    assert VD.check(doc, deep=True) == []


def test_the_moved_wall_has_no_collinear_continuation():
    """The demo picks a wall with no collinear continuation, and says why: a
    continuation would be SHEARED by a pure vertex move. This pins that the
    fixture wall really is such a wall, so the test above is exercising the
    legal case and not passing by luck."""
    doc = json.loads((EXAMPLES / "symmetricP1.json").read_text("utf-8"))
    wall = _shared_wall(doc, "Lounge", "Front Porch", horizontal=True)
    pos = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    (x1, y1), (x2, y2) = pos[wall["v1"]], pos[wall["v2"]]
    dx, dy = x2 - x1, y2 - y1
    for other in doc["walls"]:
        if other["id"] == wall["id"]:
            continue
        if not ({other["v1"], other["v2"]} & {wall["v1"], wall["v2"]}):
            continue
        (a, b), (c, d) = pos[other["v1"]], pos[other["v2"]]
        assert abs((c - a) * dy - (d - b) * dx) > 1e-6, (
            f"{other['id']} continues {wall['id']} -- the pure vertex move "
            f"would shear it")


# --------------------------------------------------------------------------
# the editor claim -- dragging a wall body moves vertices
# --------------------------------------------------------------------------
class _Ev:
    """A press / move event good enough for WallItem's handlers."""

    def __init__(self, pt, mods=NOMOD):
        self._pt, self._mods = QPointF(*pt), mods

    def button(self):
        return Qt.MouseButton.LeftButton

    def modifiers(self):
        return self._mods

    def scenePos(self):
        return self._pt

    def accept(self):
        pass

    def ignore(self):
        pass


def _wall(fp, scene, x1, y1, x2, y2, floor=None):
    w = fp.WallItem(QPointF(x1, y1), QPointF(x2, y2), "interior")
    if floor is not None:
        w.floor = floor
    scene.addItem(w)
    return w


def _tee_scene(fp, scene):
    """A horizontal wall, its collinear continuation past the right end, and a
    perpendicular wall dropping from the same corner.

        A ---------+--------- B      (B continues A's line)
                   |
                   C

    Every case of the split rule meets at that one corner: C may share it, B
    must not."""
    a = _wall(fp, scene, 0, 0, 120, 0)
    b = _wall(fp, scene, 120, 0, 240, 0)
    c = _wall(fp, scene, 120, 0, 120, 120)
    fp.rebuild_all_walls(scene)
    return a, b, c


def _body_drag(wall, dx, dy, steps=2):
    """Press the wall's middle and drag by (dx, dy) in scene units."""
    mid = ((wall.p1.x() + wall.p2.x()) / 2, (wall.p1.y() + wall.p2.y()) / 2)
    wall._mode = None
    wall.mousePressEvent(_Ev(mid))
    assert wall._mode == "move", "expected a body slide, not an end grab"
    for k in range(1, steps + 1):
        wall.mouseMoveEvent(_Ev((mid[0] + dx * k / steps,
                                 mid[1] + dy * k / steps)))


def test_drag_promotes_a_coincident_end_to_a_shared_vertex(fp, scene):
    """The 0.6" coincidence discovery becomes real sharing at drag start.

    Before P3.3 the perpendicular neighbour followed because a scan found its
    coordinates near the corner and assigned new ones every mouse event. Now its
    end IS the corner -- asserted with `is`, because equal coordinates are
    exactly what the old code already produced and would not distinguish the
    two worlds."""
    a, _b, c = _tee_scene(fp, scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))

    assert a.end_vertex("p2") is c.end_vertex("p1"), (
        "the coincident end was not promoted to the corner's vertex")
    assert a._promoted == 1


def test_a_promoted_corner_follows_the_drag(fp, scene):
    a, _b, c = _tee_scene(fp, scene)
    _body_drag(a, 0, 12)

    assert a.p2.y() == pytest.approx(12)
    assert c.p1.y() == pytest.approx(12), "the shared corner did not carry"
    assert c.p2.y() == pytest.approx(120), "the far end must not move"
    assert a.end_vertex("p2") is c.end_vertex("p1"), "sharing broke mid-drag"


def test_moving_a_corner_keeps_it_the_same_corner(fp, scene):
    """A MOVE IS NOT A SPLIT: the dragged corner keeps its identity, and the
    neighbour promoted onto it is still holding the very same object.

    CONVERTED AT P4.5 from `assert split_count() == before`. That watched for
    the absence of split-on-write; with the mechanism retired it could never
    have failed again. What it was reaching for is that the corner SURVIVES
    the drag as one corner, and that is asserted here two ways -- the uid is
    stable (identity as the document sees it) and the neighbour's end is the
    same Python object (identity as the scene holds it). Strictly stronger:
    a fresh corner minted by any route at all fails this."""
    a, _b, c = _tee_scene(fp, scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))
    shared = a.end_vertex("p2")
    uid = shared.uid
    # PRECONDITION -- there IS sharing to preserve. The press is what promotes
    # it, so this is asked after the press; and it is C, the perpendicular, that
    # may share the corner -- B is the collinear continuation the anti-shear
    # rule deliberately keeps off it (see `_tee_scene`).
    assert c.end_vertex("p1") is shared or c.end_vertex("p2") is shared,         "the tee is not shared, so this test would be about nothing"
    for k in (6, 12):
        a.mouseMoveEvent(_Ev((60, k)))
    moved = a.end_vertex("p2")
    assert (moved.x, moved.y) != (shared.x, shared.y), "the corner never moved"

    assert moved.uid == uid, "the moved corner was renamed -- that is a split"
    assert c.end_vertex("p1") is moved or c.end_vertex("p2") is moved,         "the neighbour was left on the old corner"


# ------------------------------------------------- the split rule: anti-shear
def test_a_collinear_continuation_splits_first(fp, scene):
    """Split first. The continuation keeps its own vertex, so the corner is two
    corners the instant the drag starts."""
    a, b, _c = _tee_scene(fp, scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))

    assert a.end_vertex("p2") is not b.end_vertex("p1")
    assert (b, "p1") in a._continuations


def test_a_collinear_continuation_is_never_sheared(fp, scene):
    """Shear never. The continuation runs along the line being slid off, so
    dragging its shared end sideways would swing its far end and tilt it. It
    must come out exactly where it went in, still horizontal."""
    a, b, _c = _tee_scene(fp, scene)
    b1, b2 = QPointF(b.p1), QPointF(b.p2)
    _body_drag(a, 0, 12)

    assert b.p1.y() == pytest.approx(b1.y()), "the continuation was dragged"
    assert b.p2.y() == pytest.approx(b2.y())
    assert b.p1.y() == pytest.approx(b.p2.y()), "the continuation SHEARED"
    assert (b.p1.x(), b.p2.x()) == pytest.approx((b1.x(), b2.x()))


def test_an_already_shared_continuation_is_split_at_drag_start(fp, scene):
    """The split rule has to break sharing that already exists, not merely
    decline to create it -- a corner welded by an earlier operation is exactly
    the case P3.4's weld will produce."""
    a, b, _c = _tee_scene(fp, scene)
    b.set_end_vertex("p1", a.end_vertex("p2"))       # weld them by hand
    assert a.end_vertex("p2") is b.end_vertex("p1")

    _body_drag(a, 0, 12)

    assert a.end_vertex("p2") is not b.end_vertex("p1"), "the share survived"
    assert b.p1.y() == pytest.approx(0), "the continuation followed anyway"


# ----------------------------------- the split rule: the second half (P3.4 ii)
def _body_tee_scene(fp, scene):
    """A long wall with a perpendicular wall landing on its BODY, not its end.

        A -------------+-------------
                       |
                       C

    P3.3 could only stretch C sideways from coordinates -- a body-landing had
    no vertex to be. P3.4 (ii) cuts A at the landing, which MAKES one."""
    a = _wall(fp, scene, 0, 0, 240, 0)
    c = _wall(fp, scene, 120, 0, 120, 120)
    fp.rebuild_all_walls(scene)
    return a, c


def _wall_count(fp, scene):
    return sum(1 for w in scene.items()
               if isinstance(w, fp.WallItem))


def test_a_body_landing_splits_the_wall_it_lands_on(fp, scene):
    a, c = _body_tee_scene(fp, scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))

    assert _wall_count(fp, scene) == 3, "the host wall was not split"
    assert (a.p1.x(), a.p2.x()) == (0.0, 120.0)
    assert a.end_vertex("p2") is c.end_vertex("p1"), (
        "the landing did not become a shared corner")
    assert all(kind != "tee" for *_r, kind in a._attached), (
        "the attachment should have been reclassified as a corner")


def test_the_split_landing_follows_the_drag_as_a_corner(fp, scene):
    a, c = _body_tee_scene(fp, scene)
    _body_drag(a, 0, 12)

    assert a.p2.y() == pytest.approx(12)
    assert c.p1.y() == pytest.approx(12), "the landing did not carry"
    assert c.p2.y() == pytest.approx(120), "the far end must not move"
    assert a.end_vertex("p2") is c.end_vertex("p1"), "sharing broke mid-drag"


def test_the_whole_original_span_still_slides_as_one(fp, scene):
    """Splitting the dragged wall must not leave half of it behind: the new
    segment joins the run, so the user still slides the wall they grabbed."""
    a, _c = _body_tee_scene(fp, scene)
    _body_drag(a, 0, 12)
    ys = sorted(round(w.p1.y(), 3) for w in scene.items()
                if isinstance(w, fp.WallItem) and abs(w.p1.y() - w.p2.y()) < 1)
    assert ys == [12.0, 12.0], f"the span came apart: {ys}"


def test_a_body_landing_keeps_one_corner_across_twelve_drags(fp, scene):
    """The tee branch moved its end by coordinate on EVERY mouse event; now the
    corner is real, so twelve consecutive landings leave ONE corner, not twelve.

    CONVERTED AT P4.5 from `assert split_count() == before` -- same reasoning
    as the corner-move test above. Twelve drags is the point: churn per gesture
    is what the counter was watching for, and a stable uid across twelve of
    them says it directly."""
    a, _c = _body_tee_scene(fp, scene)
    uid = a.end_vertex("p1").uid
    y0 = a.p1.y()
    for _k in range(12):
        a._mode = None
        a.mousePressEvent(_Ev((60, a.p1.y())))
        a.mouseMoveEvent(_Ev((60, a.p1.y() + 6)))
        a.mouseReleaseEvent(_Ev((60, a.p1.y() + 6)))
    # PRECONDITION -- the twelve drags actually moved the end
    assert a.p1.y() != y0, "nothing moved, so identity was never at risk"
    assert a.end_vertex("p1").uid == uid,         "the end was renamed during the landings -- one corner became many"


def test_a_landing_inside_a_doorway_now_splits_instead_of_declining(fp, scene):
    """FLIPPED AT R2c, the drag side of the same ruling. OLD: the press left the
    wall alone and the landing stayed on P3.3's coordinate path, because
    cutting a doorway in half was refused. WHY THE ASSERTION MOVED: refusing was
    defect 17's silent decline -- nothing happened and nothing said so -- and
    the primitive had to become total anyway, since a load cannot decline. The
    doorway IS cut now; the door lands on the segment holding its anchor and the
    fault is reported rather than hidden by the gesture doing nothing.

    That the scene can reach this state at all is DEFECT 25: the edit that
    creates it should say so at the time. This test pins the mechanism; the
    gesture-level report is P4.1's."""
    a = _wall(fp, scene, 0, 0, 240, 0)
    op = fp.OpeningItem(a, "door", "3280", 120.0)     # spans 104..136
    a.openings.append(op)
    _wall(fp, scene, 120, 0, 120, 120)
    fp.rebuild_all_walls(scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))

    assert _wall_count(fp, scene) == 3, "the landing was silently declined"
    assert sum(len(w.openings) for w in scene.items()
               if isinstance(w, fp.WallItem)) == 1, "the door was lost"


def test_a_press_that_splits_leaves_the_document_unchanged(fp, win):
    """The corpus guard's missing half. P3.3's press-every-wall test still
    passes -- but it passes VACUOUSLY now, because neither corpus plan has an
    unwelded body-landing, so nothing splits (measured: 0 splits on both).
    This is the case that does split, and the document must not notice: the
    scene walk already cuts walls at junctions (`split_params`), so the split
    only makes the scene agree with what the document always said."""
    from floorplanner.design.bridge import design_from_scene
    a, _c = _body_tee_scene(fp, win.scene)
    before = design_from_scene(win).to_dict()

    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))
    a._mode = None                                    # released without a drag
    fp.rebuild_all_walls(win.scene)

    assert _wall_count(fp, win.scene) == 3, "the press did not split"
    assert design_from_scene(win).to_dict() == before


# --------------------------------------------------------- same level only
def test_a_drag_never_shares_across_floors(fp, scene):
    """Defect 12a. The `_attached` scan was one of defect 12's unfiltered
    paths, where a cross-floor coincident end was wrongly dragged along -- a
    transient mis-drag that ended with the mouse-up. Promotion would make it
    permanent: a vertex carries exactly ONE level, so a shared cross-floor
    corner either violates I2 or silently rewrites a wall's level.

    Geometrically identical walls on two floors, which is precisely what a
    leaking scan cannot tell apart."""
    a = _wall(fp, scene, 0, 0, 120, 0, floor="default")
    upper = _wall(fp, scene, 120, 0, 120, 120, floor="Upper")
    same = _wall(fp, scene, 120, 0, 120, 120, floor="default")
    fp.rebuild_all_walls(scene)

    _body_drag(a, 0, 12)

    assert a.end_vertex("p2") is same.end_vertex("p1"), (
        "the SAME-floor neighbour should have been promoted")
    assert same.p1.y() == pytest.approx(12)
    assert upper.end_vertex("p1") is not a.end_vertex("p2"), (
        "a vertex was shared across levels")
    assert upper.p1.y() == pytest.approx(0), "the other floor was dragged"


def test_a_cross_floor_wall_is_not_even_scanned(fp, scene):
    """Filtered at the loop head, so it is excluded by construction rather than
    dropped later by a check someone can forget to make."""
    a = _wall(fp, scene, 0, 0, 120, 0, floor="default")
    upper = _wall(fp, scene, 120, 0, 120, 120, floor="Upper")
    fp.rebuild_all_walls(scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))

    assert all(w is not upper for w, *_ in a._attached)
    assert all(w is not upper for w, _ in a._continuations)


# ------------------------------------------- detection is still the authority
def _two_rooms_one_divider(fp, scene):
    """One 240x120 enclosure split by a SINGLE divider -- the shared-wall model,
    where a boundary between two rooms is one wall and not a wall each.

    Built by hand rather than with two `make_room` calls: those give each room
    its own wall at x=120, and then moving one of the pair changes no enclosure
    at all, so the test would pass or fail for reasons that have nothing to do
    with vertices."""
    for a, b in (((0, 0), (240, 0)), ((240, 0), (240, 120)),
                 ((240, 120), (0, 120)), ((0, 120), (0, 0))):
        scene.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    divider = fp.WallItem(QPointF(120, 0), QPointF(120, 120), "interior")
    scene.addItem(divider)
    fp.rebuild_all_walls(scene)

    rooms = []
    for name, centre in (("Left", (60, 60)), ("Right", (180, 60))):
        res = fp.detect_room(scene, QPointF(*centre))
        assert res is not None, f"{name} not detected"
        room = fp.RoomItem(name, QPointF(*centre), res[0], res[1],
                           corners=res[2])
        scene.addItem(room)
        fp.bind_room_walls(scene, room)
        rooms.append(room)
    fp.rebuild_all_walls(scene)
    return rooms[0], rooms[1], divider


def test_a_dragged_wall_resizes_the_rooms_it_borders(fp, scene):
    """The editor half of the demo: slide a party wall and the two rooms either
    side resize by equal and opposite amounts, total unchanged.

    P3.5's HEADLINE CHECK (rider 1), and the assertions did not move -- which is
    the whole point. Written at P3.3, the areas came from DETECTION: the vertex
    move gave the flood-fill correct walls to find, and a re-detection pass
    inside `rebuild_all_walls` then rebuilt both regions from scratch. That pass
    no longer exists. The same numbers now arrive because the rooms' outlines
    hold the very vertices the divider holds, so moving the divider IS moving
    two corners of each room and their areas derive from those.

    A test that survives the deletion of the machinery that used to make it pass
    is the cleanest statement of the phase there is. The `refresh_rooms` guard
    below makes the claim explicit rather than implied."""
    assert not hasattr(fp, "refresh_rooms"), \
        "the detection engine is back; this test proves nothing"
    left, right, divider = _two_rooms_one_divider(fp, scene)
    before = (left.area_sqft, right.area_sqft)
    assert divider.rooms and len(divider.rooms) == 2, "not a shared wall"

    _body_drag(divider, 12, 0)
    divider.mouseReleaseEvent(_Ev((0, 0)))

    after = (left.area_sqft, right.area_sqft)
    assert after[0] > before[0], "the left room did not grow"
    assert after[1] < before[1], "the right room did not shrink"
    assert (after[0] - before[0]) == pytest.approx(before[1] - after[1],
                                                   abs=0.01)
    assert sum(after) == pytest.approx(sum(before), abs=0.01)


# ------------------------------------------ call-site attribution (telemetry)
def test_split_telemetry_names_the_call_site(fp, win, monkeypatch):
    """P3.1 logged that an operation split; it could not say WHERE, and "which
    call sites should become real vertex moves" is a question about lines of
    code. P3.3 converts the first of them and attributes the rest."""
    from floorplanner.design import verify as V
    monkeypatch.setenv(V.ENV_VAR, "1")
    V.rebase(win)
    V.verify(win, "baseline")

    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")
    win.scene.addItem(w)
    w.p1 = QPointF(5, 5)                                    # <- the call site
    V.verify(win, "moved an end")

    where, blame = getattr(win, V.SITE_LOG_ATTR)[-1]
    assert where == "moved an end"
    assert sum(blame.values()) == 1
    (path, func, _line), = blame
    assert func == "test_split_telemetry_names_the_call_site"
    assert path.endswith("test_wall_move.py")
    V.rebase(win)


def test_attribution_skips_the_property_setter(fp):
    """Every split arrives through the `p1`/`p2` setters, so blaming those would
    put all of them on two lines and answer nothing."""
    from floorplanner import vertex as VX
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")
    before = VX.split_sites()
    w.p2 = QPointF(150, 0)
    new = {k for k, v in VX.split_sites().items() if v > before.get(k, 0)}
    assert new, "the split was not attributed at all"
    for path, func, _line in new:
        assert func not in ("p1", "p2")
        assert not path.endswith("vertex.py")


def test_relocation_carries_the_vertex_identity():
    """A moved corner is the SAME corner, so it keeps its uid -- otherwise a
    drag would silently rename every corner it touches, and P4.5 serializes
    groups by member id."""
    v = Vertex(1.0, 2.0)
    uid = v.uid
    moved = v.relocated_to(QPointF(3.0, 4.0))
    assert moved is not v
    assert moved.uid == uid
    assert (moved.x, moved.y) == (3.0, 4.0)
    assert (v.x, v.y) == (1.0, 2.0), "the old vertex was mutated in place"
    assert v.relocated_to((1.0, 2.0)) is v


def test_relocation_carries_identity_even_when_never_named():
    """DEFECT 21, found by P3.5's by-construction test and fixed at P3.5.

    The test above passes for a reason it does not state: it reads `v.uid`
    BEFORE relocating, which forces the lazy mint. `relocated_to` used to copy
    `self._uid` -- still None on a vertex nobody had named -- so a move gave the
    "same corner" a fresh identity as soon as anyone asked. Invisible while only
    the document walk read uids; a live bug at P4.5, which serializes groups by
    member id. This asserts the case the other one cannot see."""
    v = Vertex(1.0, 2.0)                       # never named: _uid is still None
    moved = v.relocated_to(QPointF(3.0, 4.0))
    assert moved.uid == v.uid, "a moved corner was silently renamed"


# ------------------------------------------------------ the COMPOSITION gate
# The standing additions, per P3.1: both apply paths, not just the one the new
# code happens to touch, plus the corpus. The Gate 2 lesson is that covering two
# paths is not the same as covering their composition.
def test_a_moved_wall_survives_the_faithful_apply(fp, win):
    """load_data -- the undo/restore path, which never welds or migrates.

    A promoted corner is scene state, not document state, so what has to survive
    is the GEOMETRY the move produced, arriving back identical through a path
    that rebuilds every wall from scratch."""
    from floorplanner.design.bridge import design_from_scene
    _left, _right, divider = _two_rooms_one_divider(fp, win.scene)
    _body_drag(divider, 12, 0)
    divider.mouseReleaseEvent(_Ev((0, 0)))

    d1 = design_from_scene(win).to_dict()
    win.load_data(json.loads(json.dumps(d1)))
    assert design_from_scene(win).to_dict() == d1


def test_a_moved_wall_survives_the_converting_apply(fp, win, tmp_path):
    """open_document -- the migrating path, which welds. Composed all the way
    out to a legacy v4 export and back, as the Gate 2 regression does."""
    from floorplanner.design.validate import check
    _left, _right, divider = _two_rooms_one_divider(fp, win.scene)
    _body_drag(divider, 12, 0)
    divider.mouseReleaseEvent(_Ev((0, 0)))
    areas = {r.name: r.area_sqft for r in win.scene.items()
             if isinstance(r, fp.RoomItem)}

    p = tmp_path / "moved.json"
    win.save_path(str(p))
    win.load_path(str(p))
    assert not win._is_dirty()
    assert check(json.loads(p.read_text(encoding="utf-8")), deep=True) == []

    v4 = tmp_path / "moved.v4.json"
    win.export_legacy_v4_path(str(v4))
    win.load_path(str(v4))
    assert win._conversion["ends_moved"] == 0, "our own export needed repair"
    after = {r.name: r.area_sqft for r in win.scene.items()
             if isinstance(r, fp.RoomItem)}
    for name, sf in areas.items():
        assert after[name] == pytest.approx(sf, abs=0.1), f"{name} moved"


@pytest.mark.parametrize("plan", ["sample_plan.json", "planc1.json"])
def test_pressing_every_wall_changes_nothing_across_the_corpus(fp, win, plan):
    """The promotion runs at PRESS, before the mouse has moved -- so a press
    that is never dragged (a click, a cancelled gesture) must leave the document
    exactly as it found it.

    That is a new risk this task introduces and nothing else would catch: the
    press rewrites which vertex a neighbour's end points at, on every wall the
    user so much as clicks. It is TOPOLOGY changing while geometry does not, so
    the assertion is the whole document rather than the areas -- areas would
    survive a promotion that quietly re-pointed an end at the wrong corner, and
    the document would not.

    Zero splits is the second half of the claim: the press creates sharing, and
    creating sharing must not itself break any."""
    from floorplanner.design.bridge import design_from_scene
    win.load_path(str(EXAMPLES / plan))
    walls = [w for w in win.scene.items()
             if isinstance(w, fp.WallItem)]
    assert walls, "the corpus plan has no walls"

    before = design_from_scene(win).to_dict()
    # every wall end, by OBJECT identity, before the presses
    ends = {(id(w), a): w.end_vertex(a) for w in walls for a in ("p1", "p2")}
    for w in walls:
        w._mode = None
        w.mousePressEvent(_Ev(((w.p1.x() + w.p2.x()) / 2,
                               (w.p1.y() + w.p2.y()) / 2)))
        w._mode = None                       # released without a drag
    fp.rebuild_all_walls(win.scene)

    assert design_from_scene(win).to_dict() == before
    # CONVERTED AT P4.5 from `assert split_count() == splits`, and TWO drafts
    # of the conversion were wrong before this one -- both kept, because each
    # was wrong about something real.
    #   (a) "every end holds the SAME object afterwards" forbids the PROMOTION
    #       this test exists to exercise: a press that creates sharing
    #       re-points one end AT its neighbour's vertex, so the object changes
    #       by design.
    #   (b) "every end holds a vertex that already existed" forbids the
    #       ANTI-SHEAR SPLIT, which mints a stationary twin at press time.
    #       Measured on sample_plan: 4 ends re-minted, at (216,288) and
    #       (432,144), every one of them AT THE SAME COORDINATES, and the
    #       sharing partition re-grouped rather than shrank (8 classes before,
    #       8 after). The old counter never saw those mints because they go
    #       through `Vertex.at`, not `moved_to` -- the instrument-boundary
    #       lesson again, and the reason a conversion cannot be mechanical.
    # WHAT IS ACTUALLY TRUE, and is the boundary between press and drag: a
    # press may RE-PARTITION a corner, and may never MOVE one. So every end's
    # vertex sits where that end's vertex sat before, whatever object it is.
    # The document comparison above cannot see this: two distinct vertices at
    # the same coordinates emit an identical document.
    moved = {(w, a) for w in walls for a in ("p1", "p2")
             if (w.end_vertex(a).x, w.end_vertex(a).y)
             != (ends[(id(w), a)].x, ends[(id(w), a)].y)}
    assert not moved, f"a press moved {len(moved)} wall end(s)"
    # ...and it must have exercised the re-partition, or it proves nothing
    assert any(w.end_vertex(a) is not ends[(id(w), a)]
               for w in walls for a in ("p1", "p2")),         "no end was re-pointed at all, so this says nothing about the press"


# --------------------------------------------------------- the group boundary
def test_a_grouped_neighbour_is_promoted_like_any_other(fp, win):
    """REWRITTEN INTO ITS OPPOSITE AT P4.5, with the carve-out it pinned.

    It used to assert that a grouped coincident end followed the drag on the
    old COORDINATE path and was never promoted (`kind == "rigid"`). Its own
    docstring gave the reason: "grouping DUPLICATES a room's walls onto the
    originals, so a grouped end coincident with a dragged wall is the common
    case... promoting it would wire a group member to an outside wall
    permanently, and what a group is topologically is P4.5's question."

    Both clauses expired here. Nothing is duplicated any more, and a group is
    a membership list over real items -- so a grouped coincident end is an
    ordinary coincident end, and it promotes like any other. A corner is one
    corner regardless of what selection set happens to hold it."""
    sc = win.scene
    grouped = fp.WallItem(QPointF(120, 0), QPointF(120, 120), "interior")
    mate = fp.WallItem(QPointF(120, 120), QPointF(240, 120), "interior")
    for w in (grouped, mate):
        sc.addItem(w)
        w.setSelected(True)
    win.group_selected()
    assert grouped.group() is not None, "the wall was not grouped"
    sc.clearSelection()

    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    sc.addItem(a)
    fp.rebuild_all_walls(sc)
    _body_drag(a, 0, 12)

    assert a.end_vertex("p2") is grouped.end_vertex("p1"), (
        "a grouped neighbour was still held out of the shared corner")
    assert a._promoted == 1
    assert "rigid" not in [k for *_, k in a._attached], "the kind survived"
    # ...and it follows the drag, which is what the old test also required
    assert grouped.p1.y() == pytest.approx(12)


def _four_room_junction(fp, scene):
    """Four rooms meeting at ONE corner, with four wall ends actually AT it.

    Deliberately built from walls that END at the centre rather than crossing
    through it: a crossing shares no wall end, and the question here is about a
    corner that several rooms genuinely hold."""
    for a, b in [((0, 0), (240, 0)), ((240, 0), (240, 240)),
                 ((240, 240), (0, 240)), ((0, 240), (0, 0)),
                 ((120, 0), (120, 120)), ((120, 120), (120, 240)),
                 ((0, 120), (120, 120)), ((120, 120), (240, 120))]:
        scene.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    # WELD FIRST, or the four ends at the centre stay four separate vertices and
    # each room later welds only its OWN two -- the corner is then held by two
    # rooms, not four, and the test sails past the case it exists for. A plan
    # loaded from a v5 file arrives already sharing, which is why the
    # symmetricP1 measurement saw four holders.
    fp.weld_scene(scene)
    fp.rebuild_all_walls(scene)
    rooms = []
    for i, (cx, cy) in enumerate(((60, 60), (180, 60), (60, 180), (180, 180))):
        res = fp.detect_room(scene, QPointF(cx, cy))
        assert res is not None, f"cell {i} not detected"
        r = fp.RoomItem(f"R{i}", QPointF(cx, cy), res[0], res[1], corners=res[2])
        scene.addItem(r)
        fp.bind_room_walls(scene, r)
        rooms.append(r)
    return rooms


def _holders(fp, scene, v):
    return [r for r in scene.items()
            if isinstance(r, fp.RoomItem) and any(e.v is v for e in r.outline)]


# CORRECTED at the P4.2 mini-gate (defect 30, second cut). The first cut made
# EVERY holder follow the moved vertex -- and Patrick's screenshot caught it
# tearing a diagonal across the off-run rooms, whose boundary is the
# CONTINUATION the anti-shear split deliberately holds still. The corrected
# rule: the split makes the corner TWO corners, and each room's corner goes
# with its own boundary -- run-bordered rooms follow the moved vertex,
# continuation-bordered rooms keep the stationary one. Nobody tears.
def test_a_dragged_corner_splits_by_each_rooms_own_boundary(fp, scene):
    """Defect 30's pinned scene, asserting the CORRECTED behaviour.

    The original measurement (symmetricP1, 4-way at (582, 714)): Dining and
    Kitchen followed, Foyer and Great Room were stranded -- walls partly
    following, outlines wholly behind. The first fix blanket-followed every
    holder, which the mini-gate refuted: Foyer's boundary is the continuation,
    which stays, so dragging its corner drew a diagonal across its region.

    Correct: run-bordered rooms (R0, R2 here) follow the moved vertex;
    continuation-bordered rooms (R1, R3) keep the stationary corner the
    anti-shear split minted; every room's outline stays axis-aligned.

    Non-vacuity is built in twice: `_body_drag` asserts the press produced a
    body slide, and the corner displacement is asserted before the verdict."""
    _four_room_junction(fp, scene)
    centre = next(w.end_vertex("p2") for w in scene.items()
                  if isinstance(w, fp.WallItem)
                  and abs(w.p2.x() - 120) < 0.01 and abs(w.p2.y() - 120) < 0.01)
    held = _holders(fp, scene, centre)
    assert len(held) >= 3, f"the precondition needs 3+ holders, got {len(held)}"

    wall = next(w for w in scene.items()
                if isinstance(w, fp.WallItem)
                and abs(w.p1.x() - 0) < 0.01 and abs(w.p1.y() - 120) < 0.01)
    run_rooms = set(wall.rooms)
    assert run_rooms and len(run_rooms) < len(held), \
        "precondition: some holders must NOT border the dragged wall"
    before = (centre.x, centre.y)
    _body_drag(wall, 0, -24)
    moved = wall.end_vertex("p2")
    assert (moved.x, moved.y) != before, \
        "the drag did not move the corner -- the verdict would be vacuous"

    for r in held:
        if r in run_rooms:
            assert any(e.v is moved for e in r.outline), \
                f"{r.name} borders the dragged run but did not follow"
        else:
            assert not any(e.v is moved for e in r.outline), \
                f"{r.name} borders the continuation but was dragged off it"
            assert any(abs(e.v.x - before[0]) < 0.01
                       and abs(e.v.y - before[1]) < 0.01
                       for e in r.outline), \
                f"{r.name} lost its stationary corner"
    # and the diagonal tear the mini-gate caught can never come back: every
    # room's outline stays axis-aligned through the drag
    for r in held:
        pts = r.corners
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            assert abs(a.x() - b.x()) < 0.01 or abs(a.y() - b.y()) < 0.01, \
                f"{r.name} has a DIAGONAL edge after the drag"


# -- the P2.3 row, RULED at P4.3: STAY, superseded-by-ruling. Both of the
# row's predicted fixes failed on their own terms, and the settled anti-shear
# rule owns the topology -- "one wall stored as two segments" is
# indistinguishable from "two walls drawn end-to-end", so one rule serves
# both and it is "split first, shear never": the continuation STAYS. The
# xfail pin that held the conflict open is replaced by these two hard
# passes (the ruling's own amendment): the stay contract asserted, and the
# HEAL -- the restoration the row actually wanted, arriving through the
# document (auto_coalesce dissolving the seam) instead of the gesture.
def test_a_roomless_body_drag_moves_the_grabbed_segment_only(fp, scene):
    # (i) the stay contract, promoted from implied to asserted. The exact
    # construction the xfail pinned: a 480" room-less wall split at a
    # mid-span T, the stem welded onto the junction -- topologically the
    # undo-split state the P2.3 row described.
    w = fp.WallItem(QPointF(0, 0), QPointF(480, 0), "interior")
    scene.addItem(w)
    stem = fp.WallItem(QPointF(240, 0), QPointF(240, 120), "interior")
    scene.addItem(stem)
    fp.rebuild_all_walls(scene)
    seg = fp.split_wall_at(scene, w, QPointF(240, 0))
    assert seg is not None                       # precondition: really split
    fp.weld_wall_ends(scene, stem)               # stem joins the T vertex
    fp.rebuild_all_walls(scene)
    assert not w.rooms and not seg.rooms         # precondition: room-less
    s1, s2 = QPointF(seg.p1), QPointF(seg.p2)
    _body_drag(w, 0, 24)
    assert w.p1.y() == pytest.approx(24)
    assert w.p2.y() == pytest.approx(24), "the grabbed segment must move"
    assert seg.p1.y() == pytest.approx(s1.y()), (
        "the continuation must STAY -- the ruling's contract")
    assert seg.p2.y() == pytest.approx(s2.y())
    assert seg.p1.y() == pytest.approx(seg.p2.y()), "the continuation SHEARED"
    assert (seg.p1.x(), seg.p2.x()) == pytest.approx((s1.x(), s2.x()))


def test_the_roomless_seam_heals_and_then_drags_as_one(fp, scene):
    # (ii) the HEAL. With auto_coalesce on, the room-less DEGREE-2 collinear
    # seam an undo leaves behind dissolves at the next merge pass (every
    # gesture release runs one), and the merged wall body-drags as one --
    # which is why the row's workaround is not permanent in spirit: it
    # survives only in the shuffle / auto_coalesce-off world, where staying
    # split is honest.
    w = fp.WallItem(QPointF(0, 0), QPointF(480, 0), "interior")
    scene.addItem(w)
    fp.rebuild_all_walls(scene)
    seg = fp.split_wall_at(scene, w, QPointF(240, 0))
    assert seg is not None and not w.rooms       # the undo-shaped seam
    assert fp.SETTINGS["auto_coalesce"] is True  # precondition: the default
    fp.merge_wall(scene, w)                      # the release's own pass
    walls = [it for it in scene.items() if isinstance(it, fp.WallItem)]
    assert len(walls) == 1, "the degree-2 seam must dissolve"
    assert walls[0] is w, "the dragged/drawn wall is the survivor"
    ends = {(w.p1.x(), w.p1.y()), (w.p2.x(), w.p2.y())}
    assert ends == {(0.0, 0.0), (480.0, 0.0)}
    _body_drag(w, 0, 24)
    assert w.p1.y() == pytest.approx(24)
    assert w.p2.y() == pytest.approx(24), "the healed wall body-drags as ONE"


def test_orthogonal_stick_is_zoom_independent(fp, win):
    # defect 13's drag half, RULED at P4.2: a gesture tolerance may pick the
    # TARGET; committed geometry must derive from scene-space rules. The stick
    # threshold decides where a stretched end LANDS, so it must not read the
    # view. (The ~20px endpoint catch radius stays zoom-scaled by the same
    # ruling -- it only decides what you grabbed.)
    sc = win.scene
    a = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")
    ortho = fp.WallItem(QPointF(230, -60), QPointF(230, 60), "interior")
    sc.addItem(a)
    sc.addItem(ortho)
    fp.rebuild_all_walls(sc)
    o, u = QPointF(0, 0), QPointF(1, 0)
    results = []
    for zoom in (0.25, 1.0, 4.0):
        win.view.resetTransform()
        win.view.scale(zoom, zoom)
        results.append(a._project_to_orthogonal(o, u, 200.0))  # 30" short
    assert results[0] == results[1] == results[2], \
        f"where the end lands depends on zoom: {results}"
    # the scene-space rule is the vocabulary's own 9" (WALL_PROJECT_STICK ==
    # JOIN_TOL, the schema's gesture tolerance): 30" away never sticks...
    assert results[1] is None
    # ...and 5" away always does, at any zoom
    for zoom in (0.25, 4.0):
        win.view.resetTransform()
        win.view.scale(zoom, zoom)
        assert a._project_to_orthogonal(o, u, 225.0) == pytest.approx(230.0)


def test_a_partial_side_slide_steps_the_neighbours_outline(fp, scene):
    """The P4.2 mini-gate's third finding, pinned. The dragged run is one
    room's whole side, but a NEIGHBOUR's side extends past the run's end
    (symmetricP1: Master Suite's south side slides; Hall's top side runs on
    under Clst). One corner cannot serve two stretches that now sit on
    different lines, so it becomes TWO corners joined by an OPEN step edge
    -- and nothing tears diagonal. Clst, bordered by the continuation only,
    must not move at all."""
    for a, b in [((0, 0), (240, 0)), ((0, 240), (240, 240)),
                 ((0, 0), (0, 240)), ((240, 0), (240, 240)),
                 ((0, 120), (80, 120)), ((80, 120), (160, 120)),
                 ((160, 120), (240, 120)), ((160, 0), (160, 120)),
                 ((80, 120), (80, 240))]:
        scene.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    fp.weld_scene(scene)
    fp.rebuild_all_walls(scene)
    rooms = {}
    for name, (cx, cy) in {"A": (80, 60), "B": (40, 180),
                           "Hall": (160, 180), "Clst": (200, 60)}.items():
        res = fp.detect_room(scene, QPointF(cx, cy))
        assert res is not None, f"{name} not detected"
        r = fp.RoomItem(name, QPointF(cx, cy), res[0], res[1], corners=res[2])
        scene.addItem(r)
        fp.bind_room_walls(scene, r)
        rooms[name] = r
    clst_before = [(p.x(), p.y()) for p in rooms["Clst"].corners]
    wall = next(w for w in scene.items() if isinstance(w, fp.WallItem)
                and abs(w.p1.y() - 120) < 0.01 and abs(w.p2.y() - 120) < 0.01
                and max(w.p1.x(), w.p2.x()) <= 80.01)
    assert {r.name for r in wall.rooms} == {"A", "B"}   # precondition
    _body_drag(wall, 0, 24)
    assert abs(wall.p1.y() - 144) < 0.01, "precondition: the drag moved"
    for r in rooms.values():
        pts = r.corners
        for i in range(len(pts)):
            pa, pb = pts[i], pts[(i + 1) % len(pts)]
            assert (abs(pa.x() - pb.x()) < 0.01
                    or abs(pa.y() - pb.y()) < 0.01), (
                f"{r.name} tore diagonal: "
                f"({pa.x():.1f},{pa.y():.1f})->({pb.x():.1f},{pb.y():.1f})")
    hall = rooms["Hall"]
    hc = [(round(p.x(), 1), round(p.y(), 1)) for p in hall.corners]
    assert (160.0, 144.0) in hc and (160.0, 120.0) in hc, \
        f"Hall did not gain the step: {hc}"
    n = len(hall.outline)
    step = next((e for i, e in enumerate(hall.outline)
                 if {(round(e.v.x, 1), round(e.v.y, 1)),
                     (round(hall.outline[(i + 1) % n].v.x, 1),
                      round(hall.outline[(i + 1) % n].v.y, 1))}
                 == {(160.0, 144.0), (160.0, 120.0)}), None)
    assert step is not None and step.wall is None, "the step must be OPEN"
    assert [(p.x(), p.y()) for p in rooms["Clst"].corners] == clst_before, \
        "Clst borders only the continuation and must not move"


# --------------------------------------------------------------------------
# P4.5: the endpoint drag joins the vertex ops (the P3.1 shim, writer 4 of 4)
# --------------------------------------------------------------------------
def _press_move_release(wall, points, mods=Qt.KeyboardModifier.NoModifier):
    """Drive one gesture directly on the item, sampling identity per event.

    Direct rather than through the `drag` fixture on purpose: what is under
    test is what each MOUSE-MOVE EVENT does to identity, so the events have to
    be individually addressable."""
    class _Ev:
        def __init__(self, p):
            self._p = p

        def scenePos(self):
            return self._p

        def button(self):
            return Qt.MouseButton.LeftButton

        def modifiers(self):
            return mods

        def accept(self):
            pass

        def ignore(self):
            pass

    wall.mousePressEvent(_Ev(points[0]))
    seen = []
    for p in points[1:]:
        wall.mouseMoveEvent(_Ev(p))
        seen.append(wall.end_vertex("p2"))
    wall.mouseReleaseEvent(_Ev(points[-1]))
    return seen


def _corner_pair(fp, scene):
    """Two walls welded at (120, 0) -- so there is a shared corner to leave."""
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b = fp.WallItem(QPointF(120, 0), QPointF(120, 96), "interior")
    scene.addItem(a)
    scene.addItem(b)
    fp.weld_scene(scene)
    fp.rebuild_all_walls(scene)
    return a, b


def test_an_endpoint_drag_detaches_once_per_gesture_not_once_per_event(
        fp, scene):
    """THE SPLIT BELONGS TO THE GESTURE, NOT TO THE EVENT.

    Assigning `p1`/`p2` is split-on-write, so the old endpoint drag minted a
    fresh `Vertex` -- and a fresh uid -- on every mouse-move event that moved
    the end, re-seating the end's opening anchors each time. The semantics were
    right and are unchanged: an endpoint drag DETACHES this end and leaves
    anything sharing the corner where it was. What is under test is that the
    detach happens ONCE and the corner is then RELOCATED, identity intact."""
    a, b = _corner_pair(fp, scene)
    assert a.end_vertex("p2") is b.end_vertex("p1"), \
        "precondition: the two walls share the corner being dragged"
    shared = b.end_vertex("p1")

    seen = _press_move_release(
        a, [QPointF(120, 0)] + [QPointF(120 + 6 * i, 0) for i in range(1, 8)])

    assert a._mode is None, "the gesture ended"
    moved = [v for v in seen if v is not shared]
    assert moved, "precondition: the drag actually moved the end off the corner"
    # ONE detached corner for the whole gesture, whatever the event count
    assert len({v.uid for v in moved}) == 1, \
        f"the end changed identity {len({v.uid for v in moved})} times in one drag"
    # ...and the neighbour never moved, which is what "detach" means
    assert b.end_vertex("p1") is shared
    assert (b.p1.x(), b.p1.y()) == (120.0, 0.0)
    assert a.end_vertex("p2") is not b.end_vertex("p1")
    assert a.p2.x() == pytest.approx(162.0)


def test_pressing_an_endpoint_without_moving_leaves_the_corner_shared(
        fp, scene):
    """The detach is LAZY, and that is behaviour worth keeping rather than an
    accident of the old setter: `moved_to` returned `self` unchanged on a
    zero-length move, so a press-and-release never took a corner apart. A
    detach-at-press would have broken a corner on a click."""
    a, b = _corner_pair(fp, scene)
    shared = a.end_vertex("p2")
    assert shared is b.end_vertex("p1"), "precondition: the corner is shared"

    seen = _press_move_release(a, [QPointF(120, 0), QPointF(120, 0)])

    assert a._mode is None
    assert seen, "precondition: at least one move event was delivered"
    assert all(v is shared for v in seen), \
        "a gesture that moved nothing still took the corner apart"
    assert a.end_vertex("p2") is b.end_vertex("p1")


def test_the_endpoint_drag_runs_on_the_same_applier_as_the_body_drag(fp, scene):
    """Row 42 names THREE structurally identical corner-appliers as a
    Phase-6 consolidation candidate. This change must not make it four: the
    endpoint drag now uses `_DragVertex` -- the body drag's applier -- and
    differs only in WHAT IT GATHERS (one deliberately detached end, rather
    than every end on the corner). The gather is where body and endpoint
    drags should differ; the application is not."""
    from floorplanner.walls import _DragVertex
    a, _b = _corner_pair(fp, scene)
    _press_move_release(a, [QPointF(120, 0), QPointF(150, 0), QPointF(162, 0)])
    # the gesture cleared it on release, so re-run one press+move and look
    a.mousePressEvent(type("E", (), {
        "scenePos": lambda s: QPointF(162, 0),
        "button": lambda s: Qt.MouseButton.LeftButton,
        "modifiers": lambda s: Qt.KeyboardModifier.NoModifier,
        "accept": lambda s: None, "ignore": lambda s: None})())
    assert a._mode in ("p1", "p2"), "precondition: an endpoint drag started"
    a.mouseMoveEvent(type("E", (), {
        "scenePos": lambda s: QPointF(180, 0),
        "button": lambda s: Qt.MouseButton.LeftButton,
        "modifiers": lambda s: Qt.KeyboardModifier.NoModifier,
        "accept": lambda s: None, "ignore": lambda s: None})())
    assert isinstance(a._ep_move, _DragVertex), \
        "the endpoint drag grew its own applier instead of joining the existing one"
    assert len(a._ep_move.ends) == 1, \
        "an endpoint drag must carry exactly the end it grabbed"
