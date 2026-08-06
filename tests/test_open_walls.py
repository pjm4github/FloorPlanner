"""'Detach wall from room' unlocks a wall's corners (it stays part of the
room); pulling a corner away from its neighbour opens just that side, and the
side closes again when the gap is filled.

REWRITTEN AT P3.5, and the whole file's mechanism moved at once, so the
justification is stated here rather than repeated per test.

OLD: an open side was an ITEM. `refresh_rooms` re-detected the room, failed
(flood-fill escapes through the gap), fell back to `reloop_open_room` to
rebuild the corner loop from the room's own walls, and `bind_room_walls`
interposed a dashed placeholder item across each vacated stretch. Every
assertion below therefore counted those items in the scene.

NEW: an open side is a FACT ABOUT THE OUTLINE. The outline is stored and holds
the walls' own corner vertices, so pulling a corner away leaves the room's shape
and area exactly as they were -- which is what the old machinery was working to
achieve -- and the side that lost its wall is simply an edge no wall spans.
`RoomItem.open_edges()` reports them; it is the scene-side twin of what
`design.bridge._rooms_of` has always emitted for the document (`wall: null`,
counted as `open_edges`).

WHAT IT COST BETWEEN P3.5 AND P3.7: the vacated stretch stopped RENDERING as a
dashed line, because nothing created the item that drew it. The document was
unchanged (it said `wall: null` before and after) and so was the room's
geometry -- only the on-screen cue was missing. CLOSED AT P3.7: the placeholder
class is deleted and the room draws a `wall: null` edge dashed itself, from the
outline, with the same pen the item used. `test_an_open_side_is_drawn_dashed`
is the receipt, and it had to be a PIXEL test -- every structural assertion in
this file stayed green for the whole life of the regression.

`test_open_wall_is_editable` is DELETED rather than rewritten: it asserted that
the dashed placeholder carried the same drag controls as a wall, and there is no
placeholder to carry them. A claim about an object nothing constructs belongs in
the log, not in a test.
"""

import json

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.vertex import Vertex

pytestmark = pytest.mark.rooms


def _room(fp, scene, x=0, y=0, w=120, h=120, name="A"):
    for a, b in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                 ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
        scene.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    fp.rebuild_all_walls(scene)
    c = QPointF(x + w / 2, y + h / 2)
    res = fp.detect_room(scene, c)
    room = fp.RoomItem(name, c, res[0], res[1], corners=res[2])
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    return room


def _right_wall(fp, room):
    return next(w for w in room.walls
                if abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1)


def _open_count(fp, scene):
    """Open SIDES of every room -- the successor to counting placeholder items."""
    return sum(len(r.open_edges()) for r in scene.items()
               if isinstance(r, fp.RoomItem))


def _shorten(fp, scene, wall, new_far=None):
    """Pull the wall's far end inward, DETACHING it from any corner it shared
    -- the endpoint drag's semantics, which is what these tests mean.

    Was `wall.p2 = ...` until P4.5. That spelling is gone; this is the same
    thing said explicitly, and it is production's own (`_drag_end_to` mints a
    fresh `Vertex` for exactly this reason). `relocated_to` would be the OTHER
    gesture -- the corner moves and everything on it follows -- and would not
    leave the room's outline behind, which is the state under test."""
    new_far = new_far or QPointF(120, 60)
    attr = "p2" if abs(wall.p2.y() - 120) < 1 else "p1"
    wall.set_end_vertex(attr, Vertex.at(QPointF(new_far)))
    wall.rebuild()
    fp.rebuild_all_walls(scene)


def _render(scene, size=200):
    """The scene rendered to a QImage, for pixel assertions (P3.4's helper)."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter
    img = QImage(size, size, QImage.Format.Format_RGB32)
    img.fill(0xFFFFFFFF)
    pr = QPainter(img)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(pr, QRectF(0, 0, size, size), QRectF(0, 0, size, size))
    pr.end()
    return img


def test_an_open_side_is_drawn_dashed(fp, scene):
    """P3.7's PIXEL HALF, and it carries the whole Known-regression row.

    The row P3.5 opened says the vacated stretch "renders as nothing rather
    than as a dashed line" -- a defect that is invisible to every structural
    assertion in this file, all of which stayed green throughout, because they
    ask the OUTLINE what is open and the outline was always right. Only a
    rendered pixel can tell "the cue is drawn" from "the cue is missing", so
    the row closes on this test and on nothing else.

    POLARITY MEASURED, NOT ASSUMED (the P3.4 junction template). On white:
      * a wall body reads 150,
      * a vacated stretch with NO cue reads 255 -- pure background, which is
        exactly the regression,
      * the dash reads ~124 with its gaps back at ~255.
    So the cue is a DARK, GAPPED line, and the `< 190` threshold from
    CLAUDE.md sits between dash and background. The wall body's 150 is not in
    play along a vacated stretch, because there is no wall there -- that is
    what open means.

    Both halves in one test, so the positive cannot go vacuous: the open side
    is dashed, and a side that is still walled shows the solid body instead."""
    room = _room(fp, scene)                         # 0,0 .. 120,120
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(scene, wall)
    _shorten(fp, scene, wall)                       # far end to y=60
    assert len(room.open_edges()) == 1              # the precondition, stated

    img = _render(scene)
    vacated = [img.pixelColor(120, y).red() for y in range(68, 118)]
    assert min(vacated) < 190, (
        f"the open side renders as nothing -- no dash on the vacated "
        f"stretch: {vacated}")
    assert max(vacated) > 200, (
        f"the open side is drawn SOLID, not dashed -- no gaps: {vacated}")

    # the negative half: the stretch the wall still spans is a solid body, and
    # a closed side is untouched by any of this
    walled = [img.pixelColor(120, y).red() for y in range(12, 49)]
    assert max(walled) - min(walled) <= 10 and max(walled) < 190, (
        f"the still-walled stretch stopped reading as a solid wall: {walled}")
    closed = [img.pixelColor(x, 0).red() for x in range(20, 101)]
    assert max(closed) - min(closed) <= 10, (
        f"a closed side picked up gaps it should not have: {closed}")


def test_detach_unlocks_corners_without_unbinding(fp, scene):
    room = _room(fp, scene)
    wall = _right_wall(fp, room)
    assert wall._ends_editable() is True              # shared walls are editable
    fp.detach_wall_from_room(scene, wall)
    assert room in wall.rooms                          # still part of the room
    assert wall._corners_unlocked and wall._ends_editable()
    assert _open_count(fp, scene) == 0                # nothing open yet


def test_pulling_a_corner_opens_that_side(fp, scene):
    room = _room(fp, scene)
    area0 = room.area_sqft
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(scene, wall)
    _shorten(fp, scene, wall)                          # pull the far end to y=60
    assert _open_count(fp, scene) == 1
    assert room in wall.rooms                          # the wall stays bound
    assert room.area_sqft == pytest.approx(area0)     # loop stays closed
    # the open side is the RIGHT one, and it is the edge the shortened wall no
    # longer spans -- not a new item interposed across the vacated stretch
    (edge,) = room.open_edges()
    assert edge.wall is wall
    assert edge.p.x() == pytest.approx(120)


def test_the_outline_does_not_move_when_a_wall_pulls_away(fp, scene):
    """The claim `reloop_open_room` existed to deliver, now free.

    It rebuilt the corner loop from the room's walls whenever detection failed,
    inserting corners wherever consecutive walls no longer met. The room's shape
    therefore depended on a repair running at the right moment. A stored outline
    is simply not disturbed by a wall that walks away from it."""
    room = _room(fp, scene)
    before = [(e.p.x(), e.p.y()) for e in room.outline]
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(scene, wall)
    _shorten(fp, scene, wall)
    assert [(e.p.x(), e.p.y()) for e in room.outline] == before
    assert len(room.outline) == 4                      # no corner inserted


def test_filling_the_gap_recloses_the_room(fp, scene):
    room = _room(fp, scene)
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(scene, wall)
    _shorten(fp, scene, wall)
    assert _open_count(fp, scene) == 1
    # extend the wall back to the corner -> gap closes
    attr = "p2" if abs(wall.p2.y() - 60) < 1 else "p1"
    wall.set_end_vertex(attr, Vertex.at(QPointF(120, 120)))
    wall.rebuild()
    fp.rebuild_all_walls(scene)
    assert _open_count(fp, scene) == 0


def test_the_document_calls_the_vacated_edge_open(fp, win):
    """The scene's `open_edges()` and the document's `wall: null` are one fact.

    This is why the placeholder could go: the v5 walk has reported an
    uncovered outline edge as open since P1.4, entirely without reference to
    a placeholder. The scene was carrying a second, item-shaped representation of
    something the document already said."""
    from floorplanner.design.bridge import design_from_scene

    sc = win.scene
    room = _room(fp, sc)
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(sc, wall)
    _shorten(fp, sc, wall)

    rep = {}
    doc = design_from_scene(win, report=rep).to_dict()
    assert rep["open_edges"] == 1
    (rm,) = doc["rooms"]
    assert sum(1 for e in rm["outline"] if e["wall"] is None) == 1
    assert len(room.open_edges()) == 1


def test_open_room_survives_save_load(fp, qapp, win):
    sc = win.scene
    room = _room(fp, sc)
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(sc, wall)
    _shorten(fp, sc, wall)
    data = json.loads(json.dumps(win.serialize()))
    assert all("open" not in w for w in data["walls"])   # nothing dashed is stored
    win.load_data(data)
    r = next(x for x in sc.items() if isinstance(x, fp.RoomItem))
    assert r.area_sqft == pytest.approx(100.0)
    assert len(r.open_edges()) == 1                       # still one open side
    assert win.serialize() == data                        # idempotent


@pytest.mark.gui
def test_corner_drag_opens_side_via_mouse(fp, win, make_room, drag):
    sc = win.scene
    room = make_room(sc, 0, 0, 120, 120, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    right = next(w for w in room.walls
                 if abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1)
    fp.detach_wall_from_room(sc, right)
    # drag the (120,120) corner up 60 scene units -> opens the lower-right side
    dy_px = int(-60 * win.view.transform().m11())
    drag(win, QPointF(120, 120), 0, dy_px, steps=4)
    assert len(room.open_edges()) == 1


@pytest.mark.gui
def test_body_slide_carries_the_open_side(fp, win, make_room, drag):
    """The old assertion was about the dashed segment translating rather than
    shearing. The segment is gone, so the claim is asserted where it now lives:
    the room's own corner, which the slide carries because the outline holds
    it."""
    sc = win.scene
    room = make_room(sc, 0, 0, 120, 120, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    right = next(w for w in room.walls
                 if abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1)
    fp.detach_wall_from_room(sc, right)
    m = win.view.transform().m11()
    drag(win, QPointF(120, 120), 0, int(-60 * m), steps=4)   # open lower-right
    assert len(room.open_edges()) == 1
    drag(win, QPointF(120, 30), int(36 * m), 0, steps=4)     # body-slide to x156
    assert right.p1.x() == pytest.approx(156, abs=3)         # translated, not
    assert right.p2.x() == pytest.approx(156, abs=3)         # sheared
    top = next(w for w in sc.items() if isinstance(w, fp.WallItem)
               and abs(w.p1.y()) < 1 and abs(w.p2.y()) < 1)
    assert max(top.p1.x(), top.p2.x()) == pytest.approx(156, abs=3)  # stretched


@pytest.mark.gui
def test_closing_gap_refuses_and_relocks(fp, win, make_room, drag):
    sc = win.scene
    room = make_room(sc, 0, 0, 120, 120, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.resize(1100, 900)
    win.show()
    # Pin an exact integer zoom rather than zoom_fit(): this test drags the
    # wall end up and then straight back down, so the two drags must be exact
    # inverses. zoom_fit() yields a fractional m that depends on the actual
    # viewport size (which differs per platform), and int(+-60*m) then
    # truncates asymmetrically -- the end lands a fraction short of the corner
    # and refuses to fuse. At an integer scale the scene<->pixel mapping is
    # exact, so the round trip closes the gap on any viewport.
    win.view.resetTransform()
    win.view.scale(2.0, 2.0)
    win.view.centerOn(QPointF(60, 60))
    right = next(w for w in room.walls
                 if abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1)
    fp.detach_wall_from_room(sc, right)
    m = win.view.transform().m11()
    drag(win, QPointF(120, 120), 0, int(-60 * m), steps=4)   # open
    assert len(room.open_edges()) == 1 and right._corners_unlocked
    drag(win, QPointF(120, 60), 0, int(60 * m), steps=4)     # drag end back down
    assert len(room.open_edges()) == 0                       # gap closed
    assert right._corners_unlocked is False                  # fused, re-locked


def test_undo_restores_closed_room(fp, qapp, win):
    sc = win.scene
    room = _room(fp, sc)
    win._commit_if_changed()
    wall = _right_wall(fp, room)
    fp.detach_wall_from_room(sc, wall)
    _shorten(fp, sc, wall)
    win._commit_if_changed()
    assert _open_count(fp, sc) == 1
    win.undo()
    assert _open_count(fp, sc) == 0
    win.redo()
    assert _open_count(fp, sc) == 1
