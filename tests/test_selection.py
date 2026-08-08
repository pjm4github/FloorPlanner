"""Rubber-band selection: only fully-enclosed items are picked, and a room
enclosed by the band gets its own edge walls selected. Selection is READ-ONLY
(P0.5 fix 4 / defect 10): an edge backed only by a longer party wall is left
unselected -- it is NOT duplicated into a new wall. The two tests below that
once asserted that duplication now assert that selection creates nothing."""
import pytest
from PyQt6.QtCore import QPointF, QRectF

pytestmark = pytest.mark.selection


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
