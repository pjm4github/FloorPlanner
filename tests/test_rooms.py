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
def test_room_label_ctrl_drag_nudges_label(fp, win, make_room, drag):
    from PyQt6.QtCore import Qt
    sc = win.scene
    room = make_room(sc, 0, 0, 240, 180, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    assert room.label_offset == QPointF(0, 0)
    # Ctrl+drag nudges only the label; the room (anchor) stays put
    drag(win, room._label_centre(), 60, -40,
         mods=Qt.KeyboardModifier.ControlModifier)
    assert room.label_offset.x() > 5
    assert room.label_offset.y() < -5
    assert room.anchor == QPointF(120, 90)       # anchor unchanged


@pytest.mark.gui
def test_room_plain_drag_moves_whole_room(fp, win, make_room, drag):
    sc = win.scene
    room = make_room(sc, 0, 0, 240, 180, "Den")
    win.set_tool(fp.TOOL_SELECT)
    win.show()
    win.zoom_fit()
    wall_y0 = [it.p1.y() for it in sc.items() if isinstance(it, fp.WallItem)]
    drag(win, room._label_centre(), 0, 48)       # plain drag moves the room
    assert room.anchor.y() > 90 + 5              # anchor moved with the room
    wall_y1 = [it.p1.y() for it in sc.items() if isinstance(it, fp.WallItem)]
    assert sum(wall_y1) > sum(wall_y0)           # the walls moved too


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
    # The overlap is this helper's POINT -- it is the input room_boolean exists
    # to resolve -- so declare it as the accepted baseline for P1.6's shadow
    # mode (FP_VERIFY_DESIGN=deep).  Without this the scene trips I11 "two
    # placed rooms overlap" at teardown, which would be true but useless: the
    # overlap was constructed here, not introduced by the operation under test.
    # Same mechanism a corrupt legacy file uses when it is loaded.
    from floorplanner.design.verify import rebase
    rebase(win)
    # win._sel_order (the selection order feeding room_boolean) is retired when
    # room_boolean is rewritten as a polygon op in v5 P3.5 (V5_MIGRATION_PLAN);
    # left as-is here and at the other _sel_order call sites in this file.
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


def _row_of_rooms(fp, sc, n, w=120, h=120):
    """`n` rooms in a row on the SHARED-WALL model -- one wall on each
    boundary, not a coincident pair. `make_room` twice would build duplicates,
    and a duplicate is a different problem from the one under test here."""
    xs = [i * w for i in range(n + 1)]
    for x in xs:                                    # verticals, incl. the party
        sc.addItem(fp.WallItem(QPointF(x, 0), QPointF(x, h), "interior"))
    for y in (0, h):                                # one long wall top + bottom
        sc.addItem(fp.WallItem(QPointF(xs[0], y), QPointF(xs[-1], y), "interior"))
    fp.rebuild_all_walls(sc)
    rooms = []
    for i in range(n):
        c = QPointF(xs[i] + w / 2, h / 2)
        res = fp.detect_room(sc, c)
        assert res is not None, f"room {i} not detected"
        r = fp.RoomItem(chr(ord("A") + i), c, res[0], res[1], corners=res[2])
        sc.addItem(r)
        fp.bind_room_walls(sc, r)
        rooms.append(r)
    return rooms


def test_boolean_spares_a_bystander_room_and_other_floors(fp, win):
    """DEFECT 8, first half. The op took its inputs' walls from
    `bounding_walls()` -- a proximity query with no floor filter -- and then
    DELETED everything it was handed. So combining two rooms removed the wall
    a third room shared with one of them (breaking that room open) and any
    wall of any other floor whose body happened to touch the band."""
    sc = win.scene
    a, b, c = _row_of_rooms(fp, sc, 3)
    upstairs = fp.WallItem(QPointF(118, 0), QPointF(118, 120), "interior")
    upstairs.floor = "Upper"                       # another floor, same place
    sc.addItem(upstairs)
    fp.rebuild_all_walls(sc)
    c_walls = set(fp.room_walls(c))

    from floorplanner.design.verify import rebase
    rebase(win)
    win._sel_order = [a, b]
    win.room_boolean("combine")

    assert c.scene() is not None and not c.open_edges(), "C was broken open"
    assert all(w.scene() is not None for w in c_walls), "a bystander wall went"
    assert upstairs.scene() is not None, "another floor's wall was deleted"


def test_boolean_keeps_exterior_walls_exterior(fp, win):
    """DEFECT 8, second half: every result wall was built as `"interior"`, so a
    combine silently downgraded 6" exterior walls to 4 1/2" interior ones. Each
    result edge now inherits from whichever input wall runs along it, exterior
    winning a tie -- an edge no input covers is genuinely new, and interior is
    the right default only there."""
    sc = win.scene
    a, b = _row_of_rooms(fp, sc, 2)
    for w in fp.room_walls(a) + fp.room_walls(b):
        w.wall_type = "exterior"
        w.rebuild()
    fp.rebuild_all_walls(sc)

    from floorplanner.design.verify import rebase
    rebase(win)
    win._sel_order = [a, b]
    win.room_boolean("combine")

    (room,) = _rooms(fp, win)
    assert room.area_sqft == pytest.approx(200.0)       # 240" x 120"
    kinds = {w.wall_type for w in fp.room_walls(room)}
    assert kinds == {"exterior"}, f"result walls downgraded: {kinds}"


@pytest.mark.xfail(strict=False, reason="register row 47 -- room_boolean builds "
                   "a duplicate wall loop per region instead of extracting, so "
                   "a fragment is not a self-contained unit; flips when "
                   "fragment converts to extract")
def test_fragment_groups_each_piece_with_its_own_walls(fp, win):
    """Each fragment is a SELF-CONTAINED UNIT: no wall belongs to two of them.

    REWRITTEN AT P4.5 (2026-08-05), and the old assertions were vacuous by
    BASIS, not merely weak. The previous verdict was `all(enclosed(r))` after
    dragging the Overlap piece clear -- and that passes on both group
    semantics, because the region the moved piece vacated is still bounded by
    the DUPLICATE walls the other two fragments were built with. It was
    measuring the neighbours, never the piece that moved. Measured: on the
    tree that strands the room completely (0 of 16 outline corners move
    against 4 of 4 walls) it still reported every fragment enclosed.

    THE MOVE IS DELIBERATELY GONE, and that is a scope reduction stated
    rather than slipped in. `bake` on this product corrupts the scene -- the
    measurement is in `docs/evidence/defect23-fragment.json`, reproducible
    with `docs/evidence/defect23_fragment_probe.py` -- and an `xfail` does not
    cover a fixture TEARDOWN error, so keeping the gesture here would make
    DEEP red for a defect this test is not the owner of. Row 47 owns the
    gesture and carries its reproduction; this test owns the PROPERTY the
    gesture needs, which is the one the test's name has always claimed.

    The verdict is a NEGATIVE assertion ("no wall is shared"), so the
    conditions for sharing are asserted first: the pieces must actually abut.
    Without that a plan of three unrelated rooms would pass it."""
    _overlapping_rooms(fp, win)
    win.room_boolean("fragment")
    sc = win.scene
    rooms = _rooms(fp, win)

    # PRECONDITION 1 -- fragment produced the partition it claims to.
    assert sorted(round(r.area_sqft) for r in rooms) == [16, 64, 64]

    # PRECONDITION 2 -- every piece is a real enclosed region, and every
    # outline edge has a wall on it, so there IS a wall set to reason about.
    for r in rooms:
        assert fp.detect_room(sc, QPointF(r.anchor.x(), r.anchor.y())) \
            is not None, f"{r.name} is not enclosed"
        assert r.open_edges() == [], f"{r.name} starts with an open edge"

    # PRECONDITION 3 -- the pieces ABUT. Without this the verdict below is
    # satisfied by three rooms that never touch, which is the vacuity the
    # negative-assertion rule exists for.
    def edges(r):
        cs = r.corners or []
        return {frozenset((_xy(cs[i]), _xy(cs[(i + 1) % len(cs)])))
                for i in range(len(cs))}

    shared_edges = sum(
        len(edges(a) & edges(b))
        for i, a in enumerate(rooms) for b in rooms[i + 1:])
    assert shared_edges >= 2, ("the fragments do not abut, so the verdict "
                               f"would be vacuous (shared edges {shared_edges})")

    # VERDICT -- a piece's walls are its own. `room_walls` is the production
    # answer to "which walls is this room made of"; two pieces sharing one
    # means neither can be moved without tearing the other, which is exactly
    # what `room_owns_walls` refuses to allow `bake` to do.
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            both = set(fp.room_walls(a)) & set(fp.room_walls(b))
            assert not both, (f"{a.name} and {b.name} share {len(both)} wall(s), "
                              f"so neither is a self-contained unit")


def _xy(p):
    return (round(p.x(), 4), round(p.y(), 4))


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


def test_building_totals_sum_included_rooms(fp, win):
    sc = win.scene
    fp.SETTINGS["cost_per_sqft"] = 200.0
    _corner_room(fp, sc, 0, 0, 144, 96, "Den")        # 96 sq ft
    _corner_room(fp, sc, 300, 0, 240, 120, "Great")   # 200 sq ft
    win._update_totals()
    assert "Sq. Feet-296" in win.totals_label.text()
    assert "$59K" in win.totals_label.text()          # 296 * 200 / 1000


def test_building_totals_excludes_unchecked_rooms(fp, win):
    sc = win.scene
    fp.SETTINGS["cost_per_sqft"] = 200.0
    _corner_room(fp, sc, 0, 0, 144, 96, "Den")
    great = _corner_room(fp, sc, 300, 0, 240, 120, "Great")
    great.properties["include_sqft"] = False
    win._update_totals()
    assert "Sq. Feet-96" in win.totals_label.text()


def test_cost_per_sqft_round_trips(fp, win):
    fp.SETTINGS["cost_per_sqft"] = 275.0
    data = json.loads(json.dumps(win.serialize()))
    assert data["settings"]["cost_per_sqft"] == pytest.approx(275.0)
    w2 = fp.MainWindow()
    try:
        w2.load_data(data)
        assert fp.SETTINGS["cost_per_sqft"] == pytest.approx(275.0)
    finally:
        w2.close()


def test_room_include_sqft_round_trips(fp, win):
    r = _corner_room(fp, win.scene, 0, 0, 144, 96, "Den")
    r.properties["include_sqft"] = False
    data = json.loads(json.dumps(win.serialize()))
    w2 = fp.MainWindow()
    try:
        w2.load_data(data)
        rr = next(it for it in w2.scene.items() if isinstance(it, fp.RoomItem))
        assert rr.properties.get("include_sqft") is False
    finally:
        w2.close()


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


def _sharing(fp, room):
    """(outline corners still holding one of the room's own walls' vertices,
    total corners) -- the by-construction property P3.5 exists for."""
    ends = {id(w.end_vertex(a)) for w in fp.room_walls(room)
            for a in ("p1", "p2")}
    return sum(1 for e in room.outline if id(e.v) in ends), len(room.outline)


def test_align_to_grid_carries_the_outline_and_the_party_wall_neighbour(fp, win):
    """P4.5. Align to grid must move the room's REGION with its walls, and must
    not tear the neighbour it shares a party wall with.

    THE RECEIPT IS THE NEIGHBOUR, not the selected rooms -- C is never
    selected, and it is C that the old code broke. Measured before the fix, on
    this exact plan: every selected room's walls went onto the grid and every
    outline stayed off it (A's outline sharing 4-of-4 -> 1-of-4 with two open
    edges, B 4-of-4 -> 0-of-4 with three), and unselected C went 4-of-4 ->
    2-of-4 and gained two dashed open edges over walls that were really there.
    Cause: `align_rooms_to_grid` assigned `p1`/`p2`, which splits on write, so
    each wall end came away on a fresh vertex and every outline holding the old
    one was left behind. After: 4-of-4 on all three, zero open edges.

    C DEFORMS RATHER THAN RESISTING, and that is ruling 2a rather than an
    accident: its corner moved, so it follows."""
    sc = win.scene
    rooms = _row_of_rooms(fp, sc, 3, 118, 118)     # 118 is off the 6" grid
    a, b, c = rooms
    for r in rooms:
        r.setSelected(r is not c)
    win._sel_order = [a, b]

    # PRECONDITIONS -- everything is coherent before, and C really does share a
    # party wall with a selected room (else "C survived" says nothing)
    for r in rooms:
        s, t = _sharing(fp, r)
        assert (s, t) == (t, t), f"{r.name} starts incoherent"
        assert r.open_edges() == [], f"{r.name} starts with an open edge"
    assert set(fp.room_walls(b)) & set(fp.room_walls(c)), \
        "B and C do not share a wall, so the neighbour claim is vacuous"
    c_before = [(round(e.p.x(), 3), round(e.p.y(), 3)) for e in c.outline]

    win.align_rooms_to_grid()

    step = fp.SETTINGS["wall_snap_in"]
    # the SELECTED rooms' walls are what the gesture promised to snap; C's own
    # far wall is not asserted here, because whether it happens to land on the
    # grid is incidental to what this test is about
    for w in set(fp.room_walls(a)) | set(fp.room_walls(b)):
        for p in (w.p1, w.p2):
            assert _on_grid(p.x(), step) and _on_grid(p.y(), step)
    for r in rooms:
        s, t = _sharing(fp, r)
        assert (s, t) == (t, t), (
            f"{r.name} outline holds {s} of {t} of its own walls' corners")
        assert r.open_edges() == [], (
            f"{r.name} has {len(r.open_edges())} open edge(s) after the align")
    # the unselected neighbour MOVED -- it followed the party corner
    assert [(round(e.p.x(), 3), round(e.p.y(), 3))
            for e in c.outline] != c_before, \
        "the neighbour's outline did not follow the corner it holds"


def test_distribute_keeps_every_room_on_its_own_walls(fp, win):
    """P4.5, and the measurement that makes this worth a test of its own: the
    old `_translate_shape` destroyed outline-to-wall sharing on EVERY room --
    4-of-4 to 0-of-4, all three -- **while translating them by zero**. Three
    contiguous rooms are already evenly spaced, so `distribute_rooms` computes
    a delta of 0 for each; assigning `p1 = QPointF(p1.x() + 0, ...)` still
    mints a fresh vertex, so a no-op gesture silently unpicked the plan and the
    NEXT wall drag stranded every room.

    So the precondition here is that the gesture moved nothing, which is what
    makes the verdict about identity alone rather than about geometry."""
    sc = win.scene
    rooms = _row_of_rooms(fp, sc, 3)
    for r in rooms:
        r.setSelected(True)
    win._sel_order = list(rooms)
    before = {r.name: [(round(e.p.x(), 3), round(e.p.y(), 3))
                       for e in r.outline] for r in rooms}
    for r in rooms:
        s, t = _sharing(fp, r)
        assert (s, t) == (t, t), f"{r.name} starts incoherent"

    win.distribute_rooms(horizontal=True)

    # PRECONDITION for the verdict -- contiguous rooms are already distributed,
    # so nothing should have moved. Identity is then the only thing at stake.
    for r in rooms:
        assert [(round(e.p.x(), 3), round(e.p.y(), 3))
                for e in r.outline] == before[r.name], \
            f"{r.name} moved; this test is about a zero-delta distribute"
    for r in rooms:
        s, t = _sharing(fp, r)
        assert (s, t) == (t, t), (
            f"{r.name} outline holds {s} of {t} of its own walls' corners "
            f"after a distribute that moved nothing")


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


def _box_walls(fp, sc, x, y, w, h):
    for p1, p2 in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                   ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
        sc.addItem(fp.WallItem(QPointF(*p1), QPointF(*p2), "interior"))
    fp.rebuild_all_walls(sc)


def test_room_tool_is_one_shot(fp, win):
    sc = win.scene
    _box_walls(fp, sc, 0, 0, 144, 96)
    win.set_tool(fp.TOOL_ROOM)
    assert win.tool == fp.TOOL_ROOM
    assert win._room_sticky is False
    res = fp.detect_room(sc, QPointF(72, 48))
    win.view._make_named_room(QPointF(72, 48), "Den", res)
    assert win.tool == fp.TOOL_SELECT            # reverted to the pointer


def test_room_tool_sticky_stays_active(fp, win):
    sc = win.scene
    _box_walls(fp, sc, 0, 0, 144, 96)
    win.set_tool(fp.TOOL_ROOM)
    win._room_sticky = True                      # as if the tool was Ctrl-set
    res = fp.detect_room(sc, QPointF(72, 48))
    win.view._make_named_room(QPointF(72, 48), "Den", res)
    assert win.tool == fp.TOOL_ROOM              # stays active


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
    """REWRITTEN AT P3.5. Old mechanism: assign new coordinates to every wall,
    then `rebuild_all_walls` re-detected the room and `set_region` replaced its
    stored path. New: the region derives from the outline, and the outline holds
    the walls' own corner vertices, so RELOCATING those corners moves the room
    -- nothing re-detects and nothing is re-assigned.

    Why the assertion moved to `relocated_to`: a bare `w.p1 = ...` is
    SPLIT-ON-WRITE by the P3.1 ruling (it mints a fresh vertex for that one wall
    end and leaves every sharer behind), so the old test was not moving walls so
    much as replacing their ends and asking detection to notice. The claim under
    test -- the region follows a wall move -- is the same; the mechanism it
    exercises is now the one the editor actually uses."""
    room = make_room(scene, 0, 0, 144, 120, "Den")
    before = room.path.boundingRect().x()
    seen, moves = set(), []
    for w in room.walls:
        for a in ("p1", "p2"):
            v = w.end_vertex(a)
            if id(v) not in seen:
                seen.add(id(v))
                moves.append((v, v.relocated_to(QPointF(v.x + 60, v.y + 48))))
    for old, new in moves:
        for w in room.walls:
            for a in ("p1", "p2"):
                if w.end_vertex(a) is old:
                    w.set_end_vertex(a, new)
        for e in room.outline:
            if e.v is old:
                e.v = new
    room.anchor = QPointF(room.anchor.x() + 60, room.anchor.y() + 48)
    fp.rebuild_all_walls(scene)
    after = room.path.boundingRect().x()
    assert after - before == pytest.approx(60, abs=6)


def test_detection_does_not_depend_on_the_view(fp, win, make_room):
    """DEFECT 13, half of it, closed and pinned.

    The defect said "detection result depends on view zoom". Measured at P3.5
    before the deletion, at zooms 0.25x - 4x: detection was already identical
    at every zoom, and what actually varied was the DRAG (the endpoint catch
    radius is `20.0 / _view_scale()`), which produced a different wall geometry
    for the same scene-space gesture and therefore a different room.

    This pins the half P3.5 owns, and it now holds structurally rather than by
    luck: `topology.enclosing_face` is a question about the wall graph, and
    there is no longer any pixel, cell or canvas rectangle anywhere in the
    answer. The drag half is retargeted -- see the P3.5 Progress log entry."""
    room = make_room(win.scene, 0, 0, 144, 120, "Den")
    seen = set()
    for z in (0.25, 0.5, 1.0, 2.0, 4.0):
        win.view.resetTransform()
        win.view.scale(z, z)
        res = fp.detect_room(win.scene, room.anchor)
        assert res is not None, f"not detected at zoom {z}"
        seen.add((round(res[1], 6),
                  tuple((round(e.p.x(), 6), round(e.p.y(), 6))
                        for e in res[2])))
    assert len(seen) == 1, f"detection differed across zooms: {seen}"


def test_detection_is_not_clipped_to_the_canvas(fp, scene, make_room):
    """DEFECT 16, closed structurally.

    Room detection used to rasterise onto a grid sized by `canvas_rect()` and
    treat anything reaching the grid's edge as unenclosed -- so a plan larger
    than the canvas silently lost its edge rooms, with no warning. Found by the
    P0.3 harness rather than by any test. The face walk has no canvas in it at
    all, which is why this closes by deletion rather than by a bounds check."""
    canvas = fp.canvas_rect()
    x = canvas.right() + 240                    # well past the canvas edge
    room = make_room(scene, x, 0, 144, 120, "Outer")
    assert room.area_sqft == pytest.approx(120.0)
    assert fp.detect_room(scene, QPointF(x + 72, 60)) is not None


def test_removing_room_unbinds_its_walls(fp, scene, make_room):
    # defect 5 (P0.5): a RoomItem removed from the scene must release its walls,
    # so no WallItem.rooms keeps a dangling reference to the deleted room.
    room = make_room(scene, 0, 0, 120, 120, "Den")
    walls = list(room.walls)
    assert walls and all(room in w.rooms for w in walls)
    scene.removeItem(room)
    assert all(room not in w.rooms for w in walls), \
        "walls still reference the removed room"
