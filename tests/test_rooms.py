"""Room detection, area, inventory, naming, and region-follows-walls."""
import json

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.rooms


def test_room_label_offset_rides_with_move(fp, win, make_room):
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 96, "Den")
    room.label_offset = QPointF(40, -20)        # as if the user dragged it
    c0 = room._label_centre()
    assert (c0.x(), c0.y()) == pytest.approx(
        (room.anchor.x() + 40, room.anchor.y() - 20))

    for w in [it for it in sc.items() if isinstance(it, fp.WallItem)]:
        w.setSelected(True)
    win.group_selected()
    g = next(it for it in sc.items() if isinstance(it, fp.GroupItem))
    g.setPos(120, 60)
    g.bake()
    c1 = room._label_centre()
    assert (c1.x() - c0.x(), c1.y() - c0.y()) == pytest.approx((120, 60), abs=4)
    assert room.label_offset == QPointF(40, -20)


def test_room_label_offset_round_trips(fp, win, make_room):
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 96, "Den")
    room.label_offset = QPointF(33, -17)
    w2 = fp.MainWindow()
    try:
        w2.load_data(json.loads(json.dumps(win.serialize())))
        r2 = next(it for it in w2.scene.items() if isinstance(it, fp.RoomItem))
        assert (r2.label_offset.x(), r2.label_offset.y()) == \
            pytest.approx((33, -17))
    finally:
        w2.close()


@pytest.mark.gui
def test_room_label_drag(fp, win, make_room, drag):
    sc = win.scene
    room = make_room(sc, 0, 0, 240, 180, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    assert room.label_offset == QPointF(0, 0)
    drag(win, room._label_centre(), 60, -40)     # drag the label right + up
    assert room.label_offset.x() > 5
    assert room.label_offset.y() < -5
    assert room.anchor == QPointF(120, 90)       # anchor unchanged


def _overlapping_rooms(fp, win):
    """Two corner-only rooms that overlap: R1 lower-left, R2 upper-right.
    R1 and R2 are each 10'x8' (80 sqft); the overlap is 4'x4' (16 sqft)."""
    sc = win.scene

    def mk(x, y, w, h, name):
        corners = [QPointF(x, y), QPointF(x + w, y),
                   QPointF(x + w, y + h), QPointF(x, y + h)]
        r = fp.RoomItem(name, QPointF(x + w / 2, y + h / 2),
                        fp.room_path_from_corners(corners),
                        fp.poly_area_sqft(corners), corners=corners)
        sc.addItem(r)
        return r

    r1 = mk(0, 0, 120, 96, "Room 1")
    r2 = mk(72, 48, 120, 96, "Room 2")
    win._sel_order = [r1, r2]
    return r1, r2


def _rooms(fp, win):
    return [it for it in win.scene.items() if isinstance(it, fp.RoomItem)]


def test_room_combine_unions(fp, win):
    _overlapping_rooms(fp, win)
    win.room_boolean("combine")
    rooms = _rooms(fp, win)
    assert len(rooms) == 1
    assert rooms[0].area_sqft == pytest.approx(144, abs=2)   # 80 + 80 - 16


def test_room_intersect_keeps_overlap(fp, win):
    _overlapping_rooms(fp, win)
    win.room_boolean("intersect")
    rooms = _rooms(fp, win)
    assert len(rooms) == 1
    assert rooms[0].area_sqft == pytest.approx(16, abs=2)


def test_room_subtract_uses_first_selected(fp, win):
    _overlapping_rooms(fp, win)
    win.room_boolean("subtract")
    rooms = _rooms(fp, win)
    assert len(rooms) == 1
    assert rooms[0].name == "Room 1"
    assert rooms[0].area_sqft == pytest.approx(64, abs=2)    # 80 - 16


def test_room_fragment_makes_three(fp, win):
    _overlapping_rooms(fp, win)
    win.room_boolean("fragment")
    rooms = _rooms(fp, win)
    assert len(rooms) == 3
    assert sorted(round(r.area_sqft) for r in rooms) == [16, 64, 64]


def test_fragment_groups_each_piece_with_its_own_walls(fp, win):
    _overlapping_rooms(fp, win)
    win.room_boolean("fragment")
    sc = win.scene
    rooms = _rooms(fp, win)
    groups = [it for it in sc.items() if isinstance(it, fp.GroupItem)]
    assert len(groups) == 3                  # each fragment is its own group
    for g in groups:                         # each group is a complete loop
        gw = [c for c in g.childItems() if isinstance(c, fp.WallItem)]
        assert fp.trace_wall_loop(gw) is not None

    def enclosed(r):
        return fp.detect_room(
            sc, QPointF(r.anchor.x(), r.anchor.y())) is not None

    assert all(enclosed(r) for r in rooms)
    # move the overlap fragment clear: every fragment stays enclosed
    overlap = next(r for r in rooms if r.name == "Overlap")
    g = next(gp for gp in groups if fp.walls_cover_room(
        {c for c in gp.childItems() if isinstance(c, fp.WallItem)}, overlap))
    g.setPos(300, 300)
    g.bake()
    assert all(enclosed(r) for r in _rooms(fp, win))


def _box(fp, room):
    from PyQt6.QtGui import QPolygonF
    return QPolygonF(room.corners).boundingRect()


def _corner_room(fp, sc, x, y, w, h, name):
    cs = [QPointF(x, y), QPointF(x + w, y), QPointF(x + w, y + h),
          QPointF(x, y + h)]
    r = fp.RoomItem(name, QPointF(x + w / 2, y + h / 2),
                    fp.room_path_from_corners(cs), fp.poly_area_sqft(cs),
                    corners=cs)
    sc.addItem(r)
    return r


def test_distribute_rooms_horizontally(fp, win):
    sc = win.scene
    r1 = _corner_room(fp, sc, 0, 0, 100, 80, "A")     # 0..100
    r2 = _corner_room(fp, sc, 120, 0, 80, 80, "B")    # 120..200 (uneven)
    r3 = _corner_room(fp, sc, 400, 0, 100, 80, "C")   # 400..500
    win._sel_order = [r1, r2, r3]
    win.distribute_rooms(horizontal=True)

    bs = sorted((_box(fp, r) for r in (r1, r2, r3)), key=lambda b: b.left())
    g1 = bs[1].left() - bs[0].right()
    g2 = bs[2].left() - bs[1].right()
    assert g1 == pytest.approx(g2, abs=1)             # equal gaps
    assert g1 == pytest.approx(110, abs=1)
    assert bs[0].left() == pytest.approx(0)           # extremes fixed
    assert bs[2].right() == pytest.approx(500)


def test_distribute_rooms_vertically(fp, win):
    sc = win.scene
    r1 = _corner_room(fp, sc, 0, 0, 80, 100, "A")
    r2 = _corner_room(fp, sc, 0, 120, 80, 80, "B")
    r3 = _corner_room(fp, sc, 0, 400, 80, 100, "C")
    win._sel_order = [r1, r2, r3]
    win.distribute_rooms(horizontal=False)

    bs = sorted((_box(fp, r) for r in (r1, r2, r3)), key=lambda b: b.top())
    assert (bs[1].top() - bs[0].bottom()) == pytest.approx(
        bs[2].top() - bs[1].bottom(), abs=1)


def test_distribute_needs_three_rooms(fp, win):
    sc = win.scene
    r1 = _corner_room(fp, sc, 0, 0, 100, 80, "A")
    r2 = _corner_room(fp, sc, 200, 0, 100, 80, "B")
    win._sel_order = [r1, r2]
    win.distribute_rooms(horizontal=True)             # < 3 -> no-op, no crash
    assert _box(fp, r2).left() == pytest.approx(200)  # unchanged


def _on_grid(v, step):
    return abs(v - round(v / step) * step) < 0.01


def test_align_rooms_to_grid_snaps_walls(fp, win):
    sc = win.scene
    corners = [(1, 2), (157, 2), (157, 98), (1, 98)]    # off-grid room
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        sc.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(79, 50))
    room = fp.RoomItem("Den", QPointF(79, 50), res[0], res[1], corners=res[2])
    sc.addItem(room)
    room.setSelected(True)
    win._sel_order = [room]

    win.align_rooms_to_grid()
    step = fp.SETTINGS["wall_snap_in"]
    walls = [it for it in sc.items() if isinstance(it, fp.WallItem)]
    for w in walls:
        for p in (w.p1, w.p2):
            assert _on_grid(p.x(), step) and _on_grid(p.y(), step)
        assert abs(w.p1.x() - w.p2.x()) < 1 or abs(w.p1.y() - w.p2.y()) < 1


def test_align_grouped_wall_loop_to_grid(fp, win):
    sc = win.scene
    corners = [(1, 2), (157, 2), (157, 98), (1, 98)]
    g = fp.GroupItem()
    sc.addItem(g)
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        wseg = fp.WallItem(QPointF(*a), QPointF(*b), "interior")
        sc.addItem(wseg)
        g.adopt(wseg)
    win._sel_order = [g]

    win.align_rooms_to_grid()
    step = fp.SETTINGS["wall_snap_in"]
    for w in [c for c in g.childItems() if isinstance(c, fp.WallItem)]:
        for p in (w.p1, w.p2):
            assert _on_grid(p.x(), step) and _on_grid(p.y(), step)


def test_align_no_selection_is_noop(fp, win):
    win._sel_order = []
    win.align_rooms_to_grid()                  # no rooms selected -> no crash


def test_refresh_rooms_drops_unwalled(fp, win):
    sc = win.scene

    def make(x, y, w, h, name):
        for p1, p2 in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                       ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
            sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
        fp.rebuild_all_walls(sc)
        res = fp.detect_room(sc, QPointF(x + w / 2, y + h / 2))
        r = fp.RoomItem(name, QPointF(x + w / 2, y + h / 2), res[0], res[1],
                        corners=res[2])
        sc.addItem(r)
        return r

    make(0, 0, 144, 96, "Den")
    orphan = make(300, 0, 144, 96, "Orphan")
    for w in list(orphan.bounding_walls()):       # leave its gray behind
        sc.removeItem(w)
    fp.rebuild_all_walls(sc)

    win.refresh_rooms_cmd()
    names = {r.name for r in sc.items() if isinstance(r, fp.RoomItem)}
    assert names == {"Den"}                       # the unwalled room is gone


def test_room_op_needs_two_rooms(fp, win):
    r1, _ = _overlapping_rooms(fp, win)
    win._sel_order = [r1]                       # only one selected
    win.room_boolean("combine")
    assert len(_rooms(fp, win)) == 2            # unchanged, no crash


def _grouped_room(fp, win, x, y, w, h, name):
    sc = win.scene
    corners = [QPointF(x, y), QPointF(x + w, y),
               QPointF(x + w, y + h), QPointF(x, y + h)]
    g = fp.GroupItem()
    sc.addItem(g)
    for i in range(4):
        wseg = fp.WallItem(corners[i], corners[(i + 1) % 4], "interior")
        sc.addItem(wseg)
        g.adopt(wseg)
    room = fp.RoomItem(name, QPointF(x + w / 2, y + h / 2),
                       fp.room_path_from_corners(corners),
                       fp.poly_area_sqft(corners), corners=corners)
    sc.addItem(room)
    return g, room


def test_room_op_resolves_grouped_rooms(fp, win):
    # the rooms are selected via their groups, not their labels
    g1, _ = _grouped_room(fp, win, 0, 0, 120, 96, "Room 1")
    g2, _ = _grouped_room(fp, win, 72, 48, 120, 96, "Room 2")
    win._sel_order = [g1, g2]
    assert len(win._selected_room_shapes()) == 2   # two groups -> two rooms
    win.room_boolean("combine")
    rooms = _rooms(fp, win)
    groups = [it for it in win.scene.items() if isinstance(it, fp.GroupItem)]
    assert len(rooms) == 1
    assert len(groups) == 0                      # source groups dissolved
    assert rooms[0].area_sqft == pytest.approx(144, abs=2)


def test_room_op_resolves_grouped_wall_loops(fp, win):
    # grouped wall-loops with NO RoomItem labels (the saved-overlap case):
    # the polygon comes from tracing the loop
    sc = win.scene

    def loop(x, y, w, h):
        corners = [QPointF(x, y), QPointF(x + w, y),
                   QPointF(x + w, y + h), QPointF(x, y + h)]
        g = fp.GroupItem()
        sc.addItem(g)
        for i in range(4):
            wseg = fp.WallItem(corners[i], corners[(i + 1) % 4], "interior")
            sc.addItem(wseg)
            g.adopt(wseg)
        return g

    g1, g2 = loop(0, 0, 120, 96), loop(72, 48, 120, 96)
    win._sel_order = [g1, g2]
    assert len(win._selected_room_shapes()) == 2
    win.room_boolean("combine")
    rooms = _rooms(fp, win)
    groups = [it for it in win.scene.items() if isinstance(it, fp.GroupItem)]
    assert len(rooms) == 1
    assert len(groups) == 0
    assert rooms[0].area_sqft == pytest.approx(144, abs=2)


def test_detect_rectangular_room(fp, scene, make_room):
    room = make_room(scene, 0, 0, 144, 120, "Den")    # 12' x 10' = 120 sqft
    assert room.area_sqft == pytest.approx(120, abs=2)
    assert room.corners is not None
    assert len(room.corners) == 4


def test_no_room_in_open_space(fp, scene, add_walls):
    # a single wall does not enclose anything
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    fp.rebuild_all_walls(scene)
    assert fp.detect_room(scene, QPointF(60, 60)) is None


def test_unique_room_name(fp, scene, make_room):
    make_room(scene, 0, 0, 144, 120, "Den")
    assert fp.unique_room_name(scene, "Den") == "Den 2"


def test_inventory_text_is_tsv_with_name(fp, scene, make_room):
    room = make_room(scene, 0, 0, 144, 120, "Den")
    txt = room.inventory_text()
    assert "Den" in txt
    assert "\t" in txt          # tab-separated for pasting into Excel


def test_inventory_counts_furnishings(fp, scene, make_room, first_furnishing):
    room = make_room(scene, 0, 0, 144, 120, "Den")
    scene.addItem(fp.FurnishingItem(first_furnishing, QPointF(72, 60), 0))
    rows = room.inventory_rows()
    names = [r[0] for r in rows]
    spec = fp.furnishing_spec(first_furnishing)
    assert any(spec["name"] in n for n in names)


def test_region_follows_wall_move(fp, scene, make_room):
    room = make_room(scene, 0, 0, 144, 120, "Den")
    before = room.path.boundingRect().x()
    for w in [i for i in scene.items() if isinstance(i, fp.WallItem)]:
        w.p1 = QPointF(w.p1.x() + 60, w.p1.y() + 48)
        w.p2 = QPointF(w.p2.x() + 60, w.p2.y() + 48)
    room.anchor = QPointF(room.anchor.x() + 60, room.anchor.y() + 48)
    fp.rebuild_all_walls(scene)
    after = room.path.boundingRect().x()
    assert after - before == pytest.approx(60, abs=6)
