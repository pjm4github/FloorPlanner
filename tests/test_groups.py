"""Group / move / ungroup behaviour, including two regressions:

1. Dragging a *grouped wall* used to run WallItem's slide + join logic on a
   group child, deleting walls on ungroup (the gui test below).
2. dissolve()'s removeFromGroup() handed item ownership back to Python; with
   no external reference the walls were garbage-collected out of the scene on
   ungroup. test_*_survives_gc forces a collection to lock this down."""
import gc
import math

import pytest
from PyQt6.QtCore import QPointF, QRectF

pytestmark = pytest.mark.groups


def _select_walls_and_furnishings(fp, scene):
    for it in list(scene.items()):
        if isinstance(it, (fp.WallItem, fp.FurnishingItem)):
            it.setSelected(True)


def test_group_move_ungroup_preserves_items(fp, win, make_room,
                                            first_furnishing, counts):
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0))
    before = counts(sc)

    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(60, 48)         # simulate a drag...
    g.bake()                 # ...folded in on release
    sc.clearSelection()
    g.setSelected(True)
    win.ungroup_selected()

    assert counts(sc) == before


def test_ungrouped_walls_survive_gc(fp, win, make_room, first_furnishing,
                                    counts):
    # the items deliberately have no external Python reference, so a GC
    # right after ungroup would destroy them if dissolve() didn't keep the
    # scene owning them
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0))
    before = counts(sc)
    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(60, 48)
    g.bake()
    sc.clearSelection()
    g.setSelected(True)
    win.ungroup_selected()
    del g
    gc.collect()
    assert counts(sc) == before


def test_bake_translates_room_region(fp, win, make_room):
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, "Den")
    before = room.path.boundingRect().x()
    for it in list(sc.items()):
        if isinstance(it, fp.WallItem):
            it.setSelected(True)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(72, 0)
    g.bake()
    after = room.path.boundingRect().x()
    assert after - before == pytest.approx(72, abs=6)


def test_extracted_room_region_follows_move(fp, win):
    # extract a room whose right edge is a longer party wall, then move the
    # group clear of that wall: the grey region/outline must follow (baked
    # on release, not live)
    sc = win.scene
    party = fp.WallItem(QPointF(120, 0), QPointF(120, 300), "interior")
    sc.addItem(party)
    for p1, p2 in [((0, 0), (120, 0)), ((120, 144), (0, 144)),
                   ((0, 144), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(60, 72))
    room = fp.RoomItem("Den", QPointF(60, 72), res[0], res[1], corners=res[2])
    sc.addItem(room)

    win.view.select_in_rect(QRectF(-12, -12, 150, 174))   # duplicates the edge
    before = room.path.boundingRect()

    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(200, 100)            # move clear of the stationary party wall
    g.bake()

    after = room.path.boundingRect()
    assert after.x() - before.x() == pytest.approx(200, abs=8)
    assert after.y() - before.y() == pytest.approx(100, abs=8)
    # the original party wall is left exactly where it was
    assert party.p1.x() == pytest.approx(120)
    assert party.p2.y() == pytest.approx(300)


def test_furnishings_ride_along(fp, win, make_room, first_furnishing):
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    f = fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0)
    sc.addItem(f)
    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(40, 30)
    g.bake()
    assert (f.scenePos().x(), f.scenePos().y()) == pytest.approx((100, 90))


def _group_room_with_furnishing(fp, win, make_room, first_furnishing):
    sc = win.scene
    make_room(sc, 0, 0, 144, 72, "Den")        # wide room
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(72, 36), 0))
    for it in list(sc.items()):
        if isinstance(it, (fp.WallItem, fp.FurnishingItem)):
            it.setSelected(True)
    win.group_selected()
    return next(i for i in sc.items() if isinstance(i, fp.GroupItem))


def test_group_rotation_turns_members_about_centre(fp, win, make_room,
                                                   first_furnishing):
    sc = win.scene
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    furn = next(c for c in g.childItems() if isinstance(c, fp.FurnishingItem))
    box0 = g.childrenBoundingRect()
    c = box0.center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))         # start angle 0
    g._apply_rotation(QPointF(c.x(), c.y() + 100), False)  # end angle 90
    g._finish_rotation()

    assert furn.rotation() == pytest.approx(90, abs=1)
    box1 = g.childrenBoundingRect()
    assert box0.width() > box0.height()        # was wide
    assert box1.height() > box1.width()        # now tall (quarter turn)
    room = next(r for r in sc.items() if isinstance(r, fp.RoomItem))
    assert room.corners is not None            # region rotated with it


def test_grouped_furnishing_hides_its_own_handle(fp, win, make_room,
                                                 first_furnishing):
    # selecting a group also selects its members (Qt couples them); a
    # grouped furnishing must not draw its own box/handle, only the group's
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    furn = next(c for c in g.childItems() if isinstance(c, fp.FurnishingItem))
    assert furn.isSelected()              # selected via the group
    assert not furn._handle_visible()     # but shows no individual handle
    g.dissolve()                          # ungrouped + still selected
    furn.setSelected(True)
    assert furn._handle_visible()         # on its own it does


def test_group_box_orients_with_rotation(fp, win, make_room, first_furnishing):
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    c = g.childrenBoundingRect().center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))
    ang = math.radians(30)
    g._apply_rotation(QPointF(c.x() + 100 * math.cos(ang),
                              c.y() + 100 * math.sin(ang)), False)
    g._finish_rotation()

    assert g._angle == pytest.approx(30, abs=1)
    local, _ = g._oriented_box()
    aabb = g.childrenBoundingRect()
    # the oriented box hugs the (rotated) content, so it is tighter than the
    # axis-aligned bounding box -- proving it turns with the group
    assert local.height() < aabb.height()


def test_group_rotation_ctrl_snaps_to_increment(fp, win, make_room,
                                                first_furnishing):
    g = _group_room_with_furnishing(fp, win, make_room, first_furnishing)
    furn = next(c for c in g.childItems() if isinstance(c, fp.FurnishingItem))
    step = fp.SETTINGS["rotate_snap_deg"]
    c = g.childrenBoundingRect().center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))         # start angle 0
    ang = math.radians(37)                                 # a non-multiple
    g._apply_rotation(
        QPointF(c.x() + 100 * math.cos(ang), c.y() + 100 * math.sin(ang)),
        True)
    g._finish_rotation()

    assert round(furn.rotation()) % int(step) == 0
    assert furn.rotation() == pytest.approx(30, abs=1)     # 37 -> nearest 15


def test_group_box_not_inflated_by_wide_window(fp, win):
    # a wide window on a room wall must not balloon the group's selection
    # box out past the room (regression: opening bounding rects were huge)
    sc = win.scene
    for p1, p2 in [((0, 0), (144, 0)), ((144, 0), (144, 96)),
                   ((144, 96), (0, 96)), ((0, 96), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    top = next(w for w in sc.items() if isinstance(w, fp.WallItem)
               and w.p1.y() == 0 and w.p2.y() == 0)
    op = fp.OpeningItem(top, "window", "9648", 72)   # 96" window on top wall
    top.openings.append(op)
    top.rebuild()
    fp.rebuild_all_walls(sc)
    for w in [it for it in sc.items() if isinstance(it, fp.WallItem)]:
        w.setSelected(True)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    box = g.childrenBoundingRect()
    # room is 96" tall; the box must hug it, not extend a window-width above
    assert box.height() < 150            # was ~210 with the old margin


@pytest.mark.gui
def test_drag_group_by_wall_preserves_items(fp, win, make_room,
                                            first_furnishing, drag, counts):
    sc = win.scene
    make_room(sc, 0, 0, 144, 120, "Den")
    sc.addItem(fp.FurnishingItem(first_furnishing, QPointF(60, 60), 0))
    before = counts(sc)

    _select_walls_and_furnishings(fp, sc)
    win.group_selected()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))

    win.show()
    win.zoom_fit()

    # press on the midpoint of the top wall -- a grouped WALL (the path that
    # used to corrupt geometry), not a furnishing
    top = min((i for i in g.childItems() if isinstance(i, fp.WallItem)),
              key=lambda w: w.p1.y() + w.p2.y())
    mid = QPointF((top.p1.x() + top.p2.x()) / 2, (top.p1.y() + top.p2.y()) / 2)
    drag(win, mid, 60, 40)

    if g.scene() is not None:
        sc.clearSelection()
        g.setSelected(True)
        win.ungroup_selected()

    assert counts(sc) == before
