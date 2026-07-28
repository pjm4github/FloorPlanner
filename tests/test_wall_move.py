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

Outlines are still produced by DETECTION here, not read off the vertices; P3.5
flips that. So the scene tests assert the areas detection arrives at, which is
the honest thing to assert while detection is the authority.
"""
import json
import pathlib

import pytest
from PyQt6.QtCore import QPointF, Qt

from floorplanner.design import validate as VD
from floorplanner.vertex import Vertex, split_count

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


def test_moving_a_corner_is_not_counted_as_a_split(fp, scene):
    """A move is not a split, and the telemetry must agree -- otherwise P3.3's
    own conversion would show up in the very log that exists to find call sites
    still needing it."""
    a, _b, _c = _tee_scene(fp, scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))
    before = split_count()
    for k in (6, 12):
        a.mouseMoveEvent(_Ev((60, k)))
    assert split_count() == before


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
               if isinstance(w, fp.WallItem) and not w.is_open)


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


def test_a_body_landing_costs_no_split_on_writes(fp, scene):
    """The telemetry point 5 predicted. The tee branch moved its end by
    coordinate on EVERY mouse event; now the corner is real and the branch is
    silent."""
    a, _c = _body_tee_scene(fp, scene)
    before = split_count()
    for _k in range(12):
        a._mode = None
        a.mousePressEvent(_Ev((60, a.p1.y())))
        a.mouseMoveEvent(_Ev((60, a.p1.y() + 6)))
        a.mouseReleaseEvent(_Ev((60, a.p1.y() + 6)))
    assert split_count() == before


def test_a_landing_inside_a_doorway_is_declined_not_forced(fp, scene):
    """The one place the scene op and the pure op differ, and only in policy:
    `topology.split_edge` raises naming P3.6, a drag declines. Neither invents
    an answer to "which segment owns a door the cut runs through"."""
    a = _wall(fp, scene, 0, 0, 240, 0)
    op = fp.OpeningItem(a, "door", "3280", 120.0)     # spans 104..136
    a.openings.append(op)
    _wall(fp, scene, 120, 0, 120, 120)
    fp.rebuild_all_walls(scene)
    a._mode = None
    a.mousePressEvent(_Ev((60, 0)))

    assert _wall_count(fp, scene) == 2, "the doorway was cut in half"
    assert any(kind == "tee" for *_r, kind in a._attached), (
        "the declined landing must stay on P3.3's coordinate path")


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

    The areas come from DETECTION, which stays authoritative until P3.5 flips
    outlines onto the stored geometry. So this asserts what detection arrives
    at -- and its arriving at the right answer is the point: the vertex move
    gives detection correct walls to find."""
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
             if isinstance(w, fp.WallItem) and not w.is_open]
    assert walls, "the corpus plan has no walls"

    before, splits = design_from_scene(win).to_dict(), split_count()
    for w in walls:
        w._mode = None
        w.mousePressEvent(_Ev(((w.p1.x() + w.p2.x()) / 2,
                               (w.p1.y() + w.p2.y()) / 2)))
        w._mode = None                       # released without a drag
    fp.rebuild_all_walls(win.scene)

    assert design_from_scene(win).to_dict() == before
    assert split_count() == splits


# --------------------------------------------------------- the group boundary
def test_a_grouped_neighbour_follows_but_is_never_promoted(fp, win):
    """Grouping DUPLICATES a room's walls onto the originals, so a grouped end
    coincident with a dragged wall is the common case, not an exotic one.

    Promoting it would wire a group member to an outside wall permanently, and
    what a group is topologically is P4.5's question -- so it keeps the old
    coordinate path and still follows the drag exactly as it does today. The
    same instinct as the `group() is None` gate that keeps grouped walls out of
    coalesce, applied one task earlier than the semantics that need it."""
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

    assert a.end_vertex("p2") is not grouped.end_vertex("p1"), (
        "a grouped wall was promoted across the group boundary")
    assert a._promoted == 0
    assert ("rigid" in [k for *_, k in a._attached]), "not even tracked"
