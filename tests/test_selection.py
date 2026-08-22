"""Rubber-band selection: only fully-enclosed items are picked, and a room
enclosed by the band gets its own edge walls selected. Selection is READ-ONLY
(P0.5 fix 4 / defect 10): an edge backed only by a longer party wall is left
unselected -- it is NOT duplicated into a new wall. The two tests below that
once asserted that duplication now assert that selection creates nothing."""
import math
import re

import pytest
from PyQt6.QtCore import QPointF, QRectF

pytestmark = pytest.mark.selection


def test_selecting_one_wall_shows_id_vertices_length_on_the_status_bar(fp, win):
    """Axis-aligned (due east, 10ft) -- no angle clause: 0/90/180/270 is
    the "nothing to report" case, per the format the angle test below
    exercises the other half of."""
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    win.scene.addItem(w)
    w.setSelected(True)
    win._apply_edit_actions()
    assert win.wall_label.text() == (
        f"Wall {w.uid}: {w.v1}(0.00, 0.00)ft -> {w.v2}(10.00, 0.00)ft"
        f"  len 10.00ft")


def test_wall_label_shows_heading_for_a_non_axis_wall(fp, win):
    """A 45-degree diagonal: the angle clause appears, and coordinates are
    decimal feet, fixed to 2 places (0065-ruling.md sec4)."""
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 100), "interior")
    win.scene.addItem(w)
    w.setSelected(True)
    win._apply_edit_actions()
    assert win.wall_label.text() == (
        f"Wall {w.uid}: {w.v1}(0.00, 0.00)ft -> {w.v2}(8.33, 8.33)ft"
        f"  len 11.79ft  angle 45.0000deg")


def test_the_angle_clause_round_trips_and_never_reads_as_a_cardinal(fp, win):
    """0068-ruling.md sec3: the prior version of this test asserted the
    printed text was not one of four hardcoded 4-decimal string literals --
    which passes at ANY fixed precision, the broken 1-decimal one included,
    so it could never have gone red against the defect it existed for
    (0068 measured this directly: simulated at .1f/.2f/.3f/.4f, the
    assertion passed at all four). This instead reads the number back out
    of the label and holds it to the invariant the clause itself enforces
    -- format-free, so it also catches a future precision regression, not
    only today's already-fixed one.

    The deviation used (0.0003deg) is chosen as an intrinsic property of
    the code under test, not a borrowed or invented magnitude: 4-decimal
    formatting's own rounding floor sits between 0.00004deg and
    0.00005deg (verified directly, see the loop below), so 0.0003deg is
    ~6x past that floor -- small enough to be a meaningful near-limit
    case, comfortably clear of any precision this format could plausibly
    round to zero."""
    # the floor this test's own margin is chosen against, not asserted in
    # production -- a companion measurement, not a duplicate of the fix
    assert f"{90.0 + 0.00004:.4f}" == "90.0000"
    assert f"{90.0 + 0.0003:.4f}" != "90.0000"

    theta = math.radians(90.0 + 0.0003)
    length = 100_000.0
    p2 = QPointF(length * math.cos(theta), length * math.sin(theta))
    w = fp.WallItem(QPointF(0, 0), p2, "interior")
    win.scene.addItem(w)
    w.setSelected(True)
    win._apply_edit_actions()
    text = win.wall_label.text()
    m = re.search(r"angle ([\d.]+)deg", text)
    assert m is not None, f"{text!r} carries no angle clause"
    shown = float(m.group(1))
    assert shown % 90.0 != 0.0, f"{text!r} prints a cardinal the predicate denied"


@pytest.mark.parametrize("p2", [
    QPointF(120, 0),      # due east   (heading 0)
    QPointF(0, 120),      # due north  (heading 90)
    QPointF(-120, 0),     # due west   (heading 180)
    QPointF(0, -120),     # due south  (heading 270)
])
def test_wall_label_omits_angle_for_all_four_cardinals(fp, win, p2):
    """0065-ruling.md sec5: the exact-string test above only exercises due
    east (heading 0); this closes the gap at the label level -- the other
    three cardinals must suppress the angle clause too, not just the
    approx-tolerant heading_deg() test in test_geometry.py."""
    w = fp.WallItem(QPointF(0, 0), p2, "interior")
    win.scene.addItem(w)
    w.setSelected(True)
    win._apply_edit_actions()
    assert "angle" not in win.wall_label.text()


def test_wall_label_clears_unless_exactly_one_wall_is_selected(fp, win):
    w1 = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    w2 = fp.WallItem(QPointF(0, 50), QPointF(120, 50), "interior")
    win.scene.addItem(w1)
    win.scene.addItem(w2)

    w1.setSelected(True)
    win._apply_edit_actions()
    assert win.wall_label.text() != ""            # exactly one: shown

    w2.setSelected(True)
    win._apply_edit_actions()
    assert win.wall_label.text() == ""             # two selected: cleared

    w1.setSelected(False)
    w2.setSelected(False)
    win._apply_edit_actions()
    assert win.wall_label.text() == ""             # none selected: cleared


def test_selects_only_fully_enclosed_walls(fp, win):
    sc = win.scene
    inside = fp.WallItem(QPointF(20, 20), QPointF(80, 20), "interior")
    crossing = fp.WallItem(QPointF(60, 60), QPointF(200, 60), "interior")
    sc.addItem(inside)
    sc.addItem(crossing)
    fp.rebuild_all_walls(sc)

    win.view.select_in_rect(QRectF(0, 0, 100, 100))

    assert inside.isSelected()
    assert not crossing.isSelected()        # one end sticks out -> excluded


def test_selects_only_fully_enclosed_furnishings(fp, win, first_furnishing):
    sc = win.scene
    near = fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0)
    far = fp.FurnishingItem(first_furnishing, QPointF(400, 400), 0)
    sc.addItem(near)
    sc.addItem(far)

    win.view.select_in_rect(QRectF(0, 0, 240, 240))

    assert near.isSelected()
    assert not far.isSelected()


def test_standalone_room_selects_four_walls_no_synthesis(fp, win, make_room):
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, "Den")
    n0 = sum(isinstance(i, fp.WallItem) for i in sc.items())

    win.view.select_in_rect(QRectF(-12, -12, 168, 144))

    n1 = sum(isinstance(i, fp.WallItem) for i in sc.items())
    assert n1 == n0                          # every edge already a wall
    assert room.isSelected()
    sel = [w for w in sc.items()
           if isinstance(w, fp.WallItem) and w.isSelected()]
    assert len(sel) == 4


def test_room_edge_on_party_wall_is_not_duplicated(fp, win):
    # REWRITTEN at P0.5 fix 4 (defect 10): this test used to assert the defect --
    # that selecting a room duplicated its party-wall edge into a new wall
    # (n0 + 1). Selection is now read-only, so it must create nothing.
    sc = win.scene
    # a vertical party wall taller than the room on its left
    party = fp.WallItem(QPointF(120, 0), QPointF(120, 300), "interior")
    sc.addItem(party)
    for p1, p2 in [((0, 0), (120, 0)), ((120, 144), (0, 144)),
                   ((0, 144), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(60, 72))
    assert res is not None
    room = fp.RoomItem("Den", QPointF(60, 72), res[0], res[1], corners=res[2])
    sc.addItem(room)
    n0 = sum(isinstance(i, fp.WallItem) for i in sc.items())

    # band encloses the room but not the top of the party wall
    win.view.select_in_rect(QRectF(-12, -12, 150, 174))

    n1 = sum(isinstance(i, fp.WallItem) for i in sc.items())
    assert n1 == n0                           # selection created nothing
    assert room.isSelected()
    assert not party.isSelected()             # the long wall is left alone
    dup = [w for w in sc.items()
           if isinstance(w, fp.WallItem) and w is not party
           and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1]
    assert dup == []                          # no synthesized duplicate edge


def test_party_wall_edge_selection_leaves_the_door_intact(fp, win):
    # REWRITTEN at P0.5 fix 4: previously asserted that the *synthesized*
    # duplicate did not stack the party wall's door. With no synthesis, assert
    # instead that selection creates nothing and the party wall + its single
    # door are untouched.
    sc = win.scene
    party = fp.WallItem(QPointF(120, 0), QPointF(120, 300), "interior")
    door = fp.OpeningItem(party, "door", "3280", 72)   # within the room edge
    party.openings.append(door)
    for p1, p2 in [((0, 0), (120, 0)), ((120, 144), (0, 144)),
                   ((0, 144), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    sc.addItem(party)
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(60, 72))
    room = fp.RoomItem("Den", QPointF(60, 72), res[0], res[1], corners=res[2])
    sc.addItem(room)
    n0 = sum(isinstance(i, fp.WallItem) for i in sc.items())

    win.view.select_in_rect(QRectF(-12, -12, 150, 174))

    n1 = sum(isinstance(i, fp.WallItem) for i in sc.items())
    assert n1 == n0                           # nothing synthesized
    assert room.isSelected()
    assert len(party.openings) == 1           # the door is untouched
    dup = [w for w in sc.items()
           if isinstance(w, fp.WallItem) and w is not party
           and abs(w.p1.x() - 120) < 1 and abs(w.p2.x() - 120) < 1]
    assert dup == []


# -- D53: a room is selected by CLICKING IT -------------------------------------
#
# These three are A1b's mechanical acceptance. The fourth item is Patrick's
# manual check and cannot live here.

@pytest.mark.gui
def test_clicking_a_room_selects_it_and_the_selection_survives_release(
        fp, win, make_room, click):
    """D53(a). The gesture the application is most often given, finally pinned.

    Before A1b this passed nowhere: `RoomItem.shape()` returned only the label
    rect, so a press on the region reached no item, and `PlanView` read that as
    blank canvas -- it panned and CLEARED the selection.
    """
    sc = win.scene
    room = make_room(sc, 0, 0, 240, 180, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    pt = QPointF(120, 150)                       # inside the region...
    assert not room._label_rect().contains(pt)   # ...and NOT on the label
    assert room.shape().contains(pt)             # precondition: it is a target
    sc.clearSelection()

    click(win, pt)

    assert room.isSelected(), "a click inside the room did not select it"
    assert sc.selectedItems() == [room]


@pytest.mark.gui
def test_pressing_a_room_does_not_clear_the_selection(fp, win, make_room, click):
    """The other half of D53(a), and the half that was ACTIVE harm: pressing a
    room's region used to run `clearSelection()` via the empty-canvas pan."""
    sc = win.scene
    a = make_room(sc, 0, 0, 200, 160, "A")
    b = make_room(sc, 400, 0, 200, 160, "B")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    b.setSelected(True)
    assert b.isSelected()                        # precondition

    click(win, QPointF(100, 130))                # press inside A's region

    assert a.isSelected(), "the clicked room is not selected"
    assert not b.isSelected(), "a plain click should replace the selection"
    assert sc.selectedItems() == [a]


@pytest.mark.gui
@pytest.mark.parametrize("mod", ["shift", "ctrl"], ids=["shift", "ctrl"])
def test_shift_and_ctrl_click_each_toggle_room_membership(
        fp, win, make_room, click, mod):
    """D53(b). BOTH modifiers, because users try both -- parametrized rather
    than duplicated so neither can be fixed while the other rots."""
    from PyQt6.QtCore import Qt
    sc = win.scene
    a = make_room(sc, 0, 0, 200, 160, "A")
    b = make_room(sc, 400, 0, 200, 160, "B")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    mods = (Qt.KeyboardModifier.ShiftModifier if mod == "shift"
            else Qt.KeyboardModifier.ControlModifier)
    sc.clearSelection()

    click(win, QPointF(100, 130))                       # plain: A only
    assert sc.selectedItems() == [a]

    click(win, QPointF(500, 130), mods=mods)            # modified: ADD B
    assert set(sc.selectedItems()) == {a, b}, f"{mod}-click did not add"

    click(win, QPointF(500, 130), mods=mods)            # modified again: DROP B
    assert sc.selectedItems() == [a], f"{mod}-click did not toggle off"


@pytest.mark.gui
def test_hit_target_ranks_by_TYPE_and_ignores_z(fp, win, make_room,
                                                first_furnishing):
    """D53's design ruling, asserted DIRECTLY: type priority, not z-order.

    A stacked point -- furnishing on wall on room -- resolves to the
    furnishing, and it keeps resolving to the furnishing when the z values are
    set ADVERSARIALLY. That second half is the whole assertion: `raise_to_front`
    puts a touched room at `_z_top * 10 + band` while furnishings stay at 3, so
    any scheme whose hit outcome depends on z is one room interaction from
    breaking.
    """
    from floorplanner.items import hit_target
    sc = win.scene
    room = make_room(sc, 0, 0, 240, 180, "Den")
    pt = QPointF(120, 140)
    wall = fp.WallItem(QPointF(60, 140), QPointF(180, 140), "interior")
    sc.addItem(wall)
    fp.rebuild_all_walls(sc)
    furn = fp.make_furnishing(first_furnishing, pt)
    sc.addItem(furn)

    # PRECONDITION: all three really are under the one point. Without this the
    # verdict below is about a stack that was never built (defect 21's lesson).
    under = set(sc.items(pt))
    assert {room, wall, furn} <= under, f"the stack is not stacked: {under}"

    assert hit_target(sc, pt) is furn

    # ADVERSARIAL Z: put the room on top of everything, exactly as
    # raise_to_front would, and the answer must not move.
    room.setZValue(9999)
    wall.setZValue(9998)
    assert hit_target(sc, pt) is furn, "z changed the answer -- it must not"

    sc.removeItem(furn)
    assert hit_target(sc, pt) is wall, "wall must outrank the room"
    sc.removeItem(wall)
    assert hit_target(sc, pt) is room, "the room is the FALLBACK target"


def test_rubber_band_is_independent_of_a_room_s_shape(fp, win, make_room):
    """D53's third acceptance: PIN `select_in_rect`'s independence.

    The census found it safe BY ACCIDENT -- the first loop type-filters to
    (WallItem, FurnishingItem, GroupItem) so a room in the results is dropped,
    and the room half uses a full scan plus `item_fully_inside`, which reads
    `item.corners` and never consults `shape()`. Accidental safety is the kind
    a later refactor removes without noticing, so it is asserted here.

    The band below INTERSECTS the room's (now region-wide) shape and does not
    contain its corners. Under `IntersectsItemShape` the room would be caught;
    under `item_fully_inside` it is not. That difference is the assertion.
    """
    sc = win.scene
    room = make_room(sc, 0, 0, 240, 180, "Den")
    band = QRectF(60, 60, 60, 60)                    # wholly INSIDE the room

    # PRECONDITION: the band really does intersect the room's shape, so a
    # shape-based implementation would select it. Without this the negative
    # verdict below is vacuous.
    assert room.shape().intersects(QPainterPath_from_rect(band)), \
        "the band does not touch the room's shape -- nothing is being tested"
    assert not all(band.contains(c) for c in room.corners)

    sc.clearSelection()
    win.view.select_in_rect(band)
    assert not room.isSelected(), \
        "select_in_rect picked a room the band merely INTERSECTS"

    sc.clearSelection()
    win.view.select_in_rect(QRectF(-40, -40, 320, 260))   # contains the room
    assert room.isSelected(), "a band containing the room must still select it"


def QPainterPath_from_rect(r):
    from PyQt6.QtGui import QPainterPath
    p = QPainterPath()
    p.addRect(r)
    return p


# -- D53: WHICH MENU does a right-click open? ----------------------------------
#
# A1b's fifth acceptance item, and the pin whose ABSENCE is why 646 green tests
# and six green CI jobs said nothing when the room menu became unreachable.
# Per TYPE, not just for the room: the room row is the one a human reported,
# and the other rows are where an unreported change would hide.

def _menu_scene(fp, win):
    """A scene holding one of every right-clickable type, and the points."""
    sc = win.scene
    cs = [QPointF(0, 0), QPointF(400, 0), QPointF(400, 300), QPointF(0, 300)]
    for i in range(4):
        sc.addItem(fp.WallItem(cs[i], cs[(i + 1) % 4], "interior"))
    fp.rebuild_all_walls(sc)
    centre = QPointF(200, 150)
    res = fp.detect_room(sc, centre)
    room = fp.RoomItem(fp.unique_room_name(sc, "Den"), centre, res[0], res[1],
                       corners=res[2])
    sc.addItem(room)
    fp.bind_room_walls(sc, room)

    inner = fp.WallItem(QPointF(100, 240), QPointF(300, 240), "interior")
    sc.addItem(inner)
    fp.rebuild_all_walls(sc)
    sc.addItem(fp.OpeningItem(inner, "door", "3280", 100.0))   # -> scene x=200
    fp.rebuild_all_walls(sc)

    furn = fp.make_furnishing(fp.furnishing_catalog()[0]["id"], QPointF(70, 70))
    sc.addItem(furn)
    sc.addItem(fp.StairItem(QPointF(330, 70)))
    grp = fp.GroupItem()
    sc.addItem(grp)
    gw = fp.WallItem(QPointF(60, 200), QPointF(140, 200), "interior")
    sc.addItem(gw)
    grp.adopt(gw)

    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    return room, {
        "room label": room.mapToScene(room._label_rect().center()),
        "room region": QPointF(200, 60),
        "wall": QPointF(280, 240),          # AWAY from the door at x=200
        "door": QPointF(200, 240),
        "furnishing": QPointF(70, 70),
        "stair": QPointF(330, 70),
        "group": QPointF(100, 200),
        "blank canvas": QPointF(-160, -160),
    }


def _menu_answered_by(fp, win, monkeypatch, scene_pt):
    """Send a real right-click; return the class that ANSWERED it."""
    from PyQt6.QtCore import QPoint
    from PyQt6.QtGui import QContextMenuEvent
    from PyQt6.QtWidgets import QApplication, QMenu
    seen = []
    monkeypatch.setattr(QMenu, "exec", lambda self, *a, **k: None)
    for cls in (fp.RoomItem, fp.WallItem, fp.OpeningItem, fp.FurnishingItem,
                fp.StairItem, fp.GroupItem, type(win.view)):
        if "contextMenuEvent" not in cls.__dict__:
            continue
        orig = cls.__dict__["contextMenuEvent"]

        def spy(self, e, _o=orig, _n=cls.__name__):
            seen.append(_n)
            return _o(self, e)
        monkeypatch.setattr(cls, "contextMenuEvent", spy)

    vp = win.view.viewport()
    p = win.view.mapFromScene(QPointF(scene_pt))
    QApplication.sendEvent(vp, QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, QPoint(p), vp.mapToGlobal(QPoint(p))))
    QApplication.processEvents()
    # a class that ENTERS and declines still logs, so the answer is the LAST
    return seen[-1] if seen else None


@pytest.mark.gui
@pytest.mark.parametrize("where,answered_by", [
    ("room label", "RoomItem"),
    ("room region", "RoomItem"),      # NEW at A1b -- see the note below
    ("wall", "WallItem"),
    ("door", "OpeningItem"),
    ("furnishing", "FurnishingItem"),
    ("stair", "StairItem"),           # subclasses FurnishingItem; MRO, measured
    ("group", "GroupItem"),
    ("blank canvas", "PlanView"),
])
def test_right_click_opens_the_menu_of_the_item_under_it(
        fp, win, monkeypatch, where, answered_by):
    """One row per type. THE ROOM ROW IS THE ONE THAT REGRESSED; the others are
    where an unreported change would hide.

    `room region` is the only row that DIFFERS from pre-A1b behaviour, and it
    is a GAIN, not a restoration: before A1b a right-click on a room's region
    gave the floor popup, because the region was not in `shape()`. The room
    menu was only ever reachable from the LABEL. Do not "restore" that.
    """
    _room, pts = _menu_scene(fp, win)
    assert _menu_answered_by(fp, win, monkeypatch, pts[where]) == answered_by


@pytest.mark.gui
@pytest.mark.parametrize("where,answered_by", [
    ("wall", "WallItem"), ("door", "OpeningItem"),
    ("furnishing", "FurnishingItem"),
])
def test_right_click_still_resolves_after_raise_to_front(
        fp, win, monkeypatch, where, answered_by):
    """THE ROW MOST LIKELY TO BITE, and it has bitten once already through the
    other virtual.

    `raise_to_front` runs on every label-drag and lifts the room to
    `_z_top * 10 + band` -- well above `WALL_Z` -- and Qt routes a context-menu
    event to the topmost item BY Z, exactly as it routes a press. A test that
    right-clicks on a freshly loaded plan passes while the real gesture fails,
    which is precisely how the first cut of A1b broke
    `dragWallFuseStraggler`. So the room is raised FIRST here.
    """
    from floorplanner.items import best_by_priority
    room, pts = _menu_scene(fp, win)
    room.raise_to_front()

    # PRECONDITION, and getting it right matters more than it looks:
    # `raise_to_front` DELIBERATELY lifts the room's OWN walls ABOVE the room
    # (`base + 4` / `base + 5`, so a wall is never hidden under its own room's
    # tint). The hazard is therefore NOT "the room outranks every wall" -- it
    # is the items the room does NOT own, which stay at their base z while the
    # room climbs to `_z_top * 10 + band`. A first draft compared against
    # max(all walls), failed on the room's own perimeter, and would have hidden
    # the real case behind a precondition that was simply wrong.
    pt = pts[where]
    target = best_by_priority(win.view.items(win.view.mapFromScene(pt)))
    assert target is not None and not isinstance(target, fp.RoomItem), \
        f"nothing outranking the room is under {where}"
    assert room.zValue() > target.zValue(), (
        f"the room ({room.zValue()}) is not above the {where} "
        f"({target.zValue()}) -- this test would be about nothing")

    assert _menu_answered_by(fp, win, monkeypatch, pt) == answered_by


# -- D53: the two affordances that had NO route off the blank canvas -----------

def _menu_route(win, menu_name, needle):
    """The (text, shortcut) of a menu-bar item, or None. Reads the LIVE menu."""
    for m in win.menuBar().actions():
        if m.menu() is None or m.text().replace("&", "") != menu_name:
            continue
        for a in m.menu().actions():
            if a.isSeparator():
                continue
            if needle.lower() in a.text().replace("&", "").lower():
                return a.text().replace("&", ""), a.shortcut().toString()
    return None


@pytest.mark.gui
def test_the_3d_viewer_is_reachable_without_blank_canvas(fp, win):
    """D53. `show_3d_view` had TWO call sites and both were blank-canvas
    right-clicks, so on a plan that fills the canvas the renderer could not be
    opened at all. It was reachable only through the hit-testing defect --
    PARASITIC REACH, the fifth instance.

    Deliberately NOT under Floors: `select_floor_popup`'s own docstring argues
    that "a chord named 'select a floor' should not offer a renderer", and that
    reasoning applies to a menu as much as to a chord.
    """
    route = _menu_route(win, "View", "3D view")
    assert route is not None, "no View menu route to the 3D viewer"
    text, key = route
    assert key == "Ctrl+3", f"expected Ctrl+3, got {key!r}"
    assert win.a_3d.isEnabled()


@pytest.mark.gui
def test_paste_room_is_reachable_beside_paste(fp, win, make_room):
    """D53. `room_clipboard` was written by the room menu's Copy room and read
    by ONE caller, reached only from the blank-canvas menu -- so Ctrl+V does not
    paste a room and there was no other way in. A1b widening the room menu made
    Copy easier to reach while Paste stayed put; this closes the asymmetry it
    created.

    The two clipboards stay SEPARATE -- joining them is a design question and
    is filed rather than answered here.
    """
    route = _menu_route(win, "Edit", "Paste room")
    assert route is not None, "no Edit menu route to Paste room"
    assert route[1] == "Ctrl+Shift+V", f"expected Ctrl+Shift+V, got {route[1]!r}"

    sc = win.scene
    room = make_room(sc, 0, 0, 240, 180, "Den")
    win.room_clipboard = win.room_template(room)
    before = sum(1 for i in sc.items() if isinstance(i, fp.RoomItem))

    win.paste_room_here()          # the menu action's slot, no click point

    after = sum(1 for i in sc.items() if isinstance(i, fp.RoomItem))
    assert after == before + 1, "Paste room from the menu pasted nothing"


@pytest.mark.gui
def test_paste_room_with_an_empty_clipboard_says_so_and_does_not_raise(fp, win):
    """The negative half, with its precondition asserted first: the clipboard
    really is empty, so "nothing was pasted" is a verdict and not an accident."""
    sc = win.scene
    win.room_clipboard = None                       # PRECONDITION
    before = sum(1 for i in sc.items() if isinstance(i, fp.RoomItem))
    win.paste_room_here()
    after = sum(1 for i in sc.items() if isinstance(i, fp.RoomItem))
    assert after == before
