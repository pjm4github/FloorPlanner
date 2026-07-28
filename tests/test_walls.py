"""Wall geometry plus door/window opening sizing and garage-door defaults."""
import pytest
from PyQt6.QtCore import QPointF, QRectF, Qt

from floorplanner.walls import merge_wall, weld_scene, weld_wall_ends

pytestmark = pytest.mark.walls

NOMOD = Qt.KeyboardModifier.NoModifier


def _draw_end(fp, win, p1, drag_to):
    """End point of a wall drawn from p1 toward drag_to (no modifiers)."""
    temp = fp.WallItem(QPointF(*p1), QPointF(*p1), "interior")
    return win.view._wall_end_point(temp, QPointF(*drag_to), NOMOD)


def test_wall_draw_aligns_end_to_orthogonal_wall(fp, win):
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior"))
    fp.rebuild_all_walls(sc)
    end = _draw_end(fp, win, (0, 102), (291, 108))
    assert end.x() == pytest.approx(300)   # x lines up with the vertical wall
    assert end.y() == pytest.approx(102)   # stays horizontal


def test_wall_draw_stays_orthogonal_not_diagonal(fp, win):
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior"))
    fp.rebuild_all_walls(sc)
    # drag toward the wall's off-axis bottom endpoint (300, 200)
    end = _draw_end(fp, win, (0, 100), (305, 195))
    assert end.y() == pytest.approx(100)   # not pulled diagonally to 200
    assert end.x() == pytest.approx(300)


def test_wall_draw_leaves_gap_when_not_meeting(fp, win):
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior"))
    fp.rebuild_all_walls(sc)
    # y is past the vertical wall's extent -> aligned x, but a gap remains
    end = _draw_end(fp, win, (0, 300), (291, 305))
    assert (end.x(), end.y()) == pytest.approx((300, 300))


def test_wall_draw_orthogonal_far_from_walls(fp, win):
    end = _draw_end(fp, win, (0, 500), (250, 540))
    assert end.y() == pytest.approx(500)   # horizontal, no off-axis pull


def test_no_autogrow_when_released_short(fp, scene):
    # a wall released short of another must NOT grow to reach it
    target = fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior")
    scene.addItem(target)
    w = fp.WallItem(QPointF(0, 100), QPointF(250, 100), "interior")
    scene.addItem(w)
    fp.rebuild_all_walls(scene)
    weld_wall_ends(scene, w)
    assert w.p2.x() == pytest.approx(250)        # stayed short, no growth
    assert target.p2.y() == pytest.approx(200)   # target wall unchanged


def test_draw_snaps_to_open_ended_wall(fp, win):
    sc = win.scene
    w = fp.WallItem(QPointF(300, 0), QPointF(300, 200), "interior")
    sc.addItem(w)
    fp.rebuild_all_walls(sc)
    assert fp.wall_endpoint_open(sc, QPointF(300, 200), ignore=(w,))  # dangling
    end = _draw_end(fp, win, (0, 102), (291, 108))
    assert end.x() == pytest.approx(300)         # lines up with its projection


def test_draw_ignores_fully_joined_wall(fp, win):
    sc = win.scene
    for a, b in [((0, 0), (200, 0)), ((200, 0), (200, 200)),
                 ((200, 200), (0, 200)), ((0, 200), (0, 0))]:
        sc.addItem(fp.WallItem(QPointF(*a), QPointF(*b), "interior"))
    fp.rebuild_all_walls(sc)
    assert not fp.wall_endpoint_open(sc, QPointF(200, 0))  # corner, not open
    end = _draw_end(fp, win, (300, 102), (211, 108))
    assert end.x() != pytest.approx(200)         # no snap to the joined wall


def test_wall_length_and_point_at(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")
    scene.addItem(w)
    assert w.length() == pytest.approx(100)
    pt = w.point_at(50)
    assert (pt.x(), pt.y()) == pytest.approx((50, 0))


def test_opening_size_from_code(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "3280", 60)
    w.openings.append(op)
    w.rebuild()
    assert op.width == pytest.approx(32)
    assert op.height == pytest.approx(80)


def test_opening_wider_than_wall_rejected(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(30, 0), "interior")
    scene.addItem(w)
    with pytest.raises(ValueError):
        fp.OpeningItem(w, "door", "3280", 15)   # 32" door on a 30" wall


def test_garage1_autosizes_to_single(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(240, 0), "interior")  # 20'
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "2880", 120)
    w.openings.append(op)
    w.rebuild()
    op.set_door_type("GARAGE-1")
    assert op.width == pytest.approx(108)        # single garage door = 9'


def test_garage2_autosizes_to_double(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(300, 0), "interior")  # 25'
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "2880", 150)
    w.openings.append(op)
    w.rebuild()
    op.set_door_type("GARAGE-2")
    assert op.width == pytest.approx(192)         # double garage door = 16'


def _coincident_pair(fp, scene):
    """Wall A (with a door) and a plain coincident wall B on the same line."""
    a = fp.WallItem(QPointF(120, 0), QPointF(120, 200), "interior")
    scene.addItem(a)
    door = fp.OpeningItem(a, "door", "3280", 100)
    a.openings.append(door)
    b = fp.WallItem(QPointF(120, 0), QPointF(120, 200), "interior")
    scene.addItem(b)
    fp.rebuild_all_walls(scene)
    return a, b, door


def test_coincident_plain_wall_opens_for_neighbor_door(fp, scene):
    a, b, door = _coincident_pair(fp, scene)
    assert b in fp.coincident_walls(scene, a)
    assert not b._path.contains(QPointF(120, 100))   # opened at the door
    assert b._path.contains(QPointF(120, 180))       # solid elsewhere
    assert len(b.openings) == 0                       # never a stacked door


def test_coincident_void_follows_slide_and_clears_on_delete(fp, scene):
    a, b, door = _coincident_pair(fp, scene)
    door.s = 150
    a.rebuild()                                       # cascades to b
    assert b._path.contains(QPointF(120, 100))        # old spot solid again
    assert not b._path.contains(QPointF(120, 150))    # new spot opened
    a.openings.remove(door)
    a.rebuild()
    assert b._path.contains(QPointF(120, 150))        # re-solidified


def test_window_bounding_rect_is_tight(fp, scene):
    # a wide opening must not inflate its bounding rect perpendicular to the
    # wall (that used to balloon any enclosing group's selection box)
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "window", "9648", 60)     # 96" wide window
    w.openings.append(op)
    w.rebuild()
    br = op.boundingRect()
    assert br.height() < 60                # ~ wall thickness + pad, not ~228


def test_door_swing_stays_within_bounding_rect(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "3280", 60)       # 32" LH door
    op.swing = -1
    w.openings.append(op)
    w.rebuild()
    br = op.boundingRect()
    # the quarter-circle swing reaches ~width on the swing side; the rect
    # must still cover it
    assert br.top() <= -op.width


def test_garage_keeps_size_when_wall_too_short(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")  # 8'4"
    scene.addItem(w)
    op = fp.OpeningItem(w, "door", "2880", 50)
    w.openings.append(op)
    w.rebuild()
    op.set_door_type("GARAGE-2")                  # 16' won't fit -> keep 28"
    assert op.width == pytest.approx(28)


# -- stretching an end: stick to an orthogonal wall's line, never fuse --------
def _stretch(fp, scene, drag_x):
    a = fp.WallItem(QPointF(0, 0), QPointF(90, 0), "interior")
    scene.addItem(a)
    a._anchor, a._axis = QPointF(0, 0), QPointF(1, 0)   # as set when grabbing p2
    return a._endpoint_target(QPointF(drag_x, 0), NOMOD)


def test_stretch_sticks_to_orthogonal_projected_line(fp, scene):
    scene.addItem(fp.WallItem(QPointF(100, 12), QPointF(100, 100), "interior"))
    t = _stretch(fp, scene, 98)                    # drag the end near x=100
    assert (t.x(), t.y()) == pytest.approx((100, 0))   # stuck to that line


def test_stretch_grid_only_when_far_from_walls(fp, scene):
    scene.addItem(fp.WallItem(QPointF(100, 12), QPointF(100, 100), "interior"))
    t = _stretch(fp, scene, 70)                    # too far to stick
    assert t.x() == pytest.approx(72)              # grid (6") only, not 100


def test_stretch_does_not_fuse_to_a_parallel_endpoint(fp, scene):
    # a collinear wall whose endpoint sits at a non-grid x=95 must NOT pull the
    # dragged end onto it -- only orthogonal projected lines stick
    scene.addItem(fp.WallItem(QPointF(95, 0), QPointF(150, 0), "interior"))
    t = _stretch(fp, scene, 95)
    assert t.x() == pytest.approx(96)              # grid-snapped, not fused


# -- a SHORT wall must keep a grabbable middle for the perpendicular slide -----
class _Press:
    def __init__(self, pt, mods=Qt.KeyboardModifier.NoModifier):
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


def test_short_wall_middle_click_body_slides(fp, scene):
    w = fp.WallItem(QPointF(100, 100), QPointF(118, 100), "interior")  # 18"
    scene.addItem(w)
    fp.rebuild_all_walls(scene)
    w._mode = None
    w.mousePressEvent(_Press((109, 100)))     # the middle of the short wall
    assert w._mode == "move"                  # body slide, not an end grab
    w._mode = None
    w.mousePressEvent(_Press((100.5, 100)))   # right at the end
    assert w._mode in ("p1", "p2")            # end still grabbable


# -- Ctrl-drag: re-angle in fixed (15 deg) increments around the anchor --------
import math  # noqa: E402

CTRL = Qt.KeyboardModifier.ControlModifier


def _angle_drag(fp, scene, to, anchor=(0, 0)):
    a = fp.WallItem(QPointF(*anchor), QPointF(120, 0), "interior")
    scene.addItem(a)
    a._anchor, a._axis = QPointF(*anchor), QPointF(1, 0)   # grabbing p2
    return a, a._endpoint_target(QPointF(*to), CTRL)


def test_ctrl_drag_snaps_to_45_degrees(fp, scene):
    _, t = _angle_drag(fp, scene, (100, 100))
    assert round(math.degrees(math.atan2(t.y(), t.x()))) == 45


def test_ctrl_drag_snaps_to_nearest_15(fp, scene):
    _, t = _angle_drag(fp, scene, (100, 20))        # ~11.3 deg -> 15
    assert round(math.degrees(math.atan2(t.y(), t.x()))) == 15


def test_ctrl_drag_grid_snaps_length(fp, scene):
    _, t = _angle_drag(fp, scene, (100, 100))
    step = fp.SETTINGS["wall_snap_in"]
    length = math.hypot(t.x(), t.y())
    assert abs(length / step - round(length / step)) < 1e-6
    assert length >= fp.MIN_WALL_LEN


def test_shift_still_free_angles(fp, scene):
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(a)
    a._anchor, a._axis = QPointF(0, 0), QPointF(1, 0)
    t = a._endpoint_target(QPointF(95, 41), Qt.KeyboardModifier.ShiftModifier)
    assert (t.x(), t.y()) == pytest.approx((96, 42))   # free, grid-only


# -- wall coalescing: collinear, overlapping, same type, within the grid -------
def test_coalesce_overlapping_same_type_walls(fp, scene):
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b = fp.WallItem(QPointF(60, 0), QPointF(204, 0), "interior")   # on 6" grid
    scene.addItem(a)
    scene.addItem(b)
    merge_wall(scene, a)
    walls = [it for it in scene.items() if isinstance(it, fp.WallItem)]
    assert len(walls) == 1
    assert (walls[0].p1.x(), walls[0].p2.x()) == pytest.approx((0, 204))


def test_no_coalesce_different_wall_types(fp, scene):
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(a)
    scene.addItem(fp.WallItem(QPointF(60, 0), QPointF(200, 0), "exterior"))
    merge_wall(scene, a)
    assert len([it for it in scene.items()
                if isinstance(it, fp.WallItem)]) == 2


def test_coalesce_merges_free_wall_into_room_wall(fp, scene, make_room):
    # a free wall laid on a room's wall coalesces into ONE shared wall that the
    # room still owns (shared-wall model -- room walls coalesce too)
    room = make_room(scene, 0, 0, 120, 120, "Den")
    rw = room.walls[0]
    free = fp.WallItem(QPointF(rw.p1), QPointF(rw.p2), rw.wall_type)
    scene.addItem(free)
    survivor = merge_wall(scene, free)
    assert rw.scene() is None                     # rw was absorbed
    assert len(room.walls) == 4                   # still one wall per edge
    assert survivor in room.walls and room in survivor.rooms


def test_coalesce_carries_openings_across(fp, scene):
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b = fp.WallItem(QPointF(60, 0), QPointF(240, 0), "interior")
    scene.addItem(a)
    scene.addItem(b)
    b.openings.append(fp.OpeningItem(b, "door", "3280", 150))
    merge_wall(scene, a)
    walls = [it for it in scene.items() if isinstance(it, fp.WallItem)]
    assert len(walls) == 1
    assert len(walls[0].openings) == 1 and walls[0].openings[0].kind == "door"


# -- welding: a drawn end fuses onto the wall it meets (T/L joint) -------------
def test_welding_an_end_onto_a_through_wall(fp, scene):
    scene.addItem(fp.WallItem(QPointF(0, 100), QPointF(200, 100), "interior"))
    stem = fp.WallItem(QPointF(100, 108), QPointF(100, 200), "interior")  # 8" gap
    scene.addItem(stem)
    fp.rebuild_all_walls(scene)
    weld_wall_ends(scene, stem)
    assert stem.p1.y() == pytest.approx(100, abs=0.01)   # welded onto the wall


def test_welding_leaves_a_far_end_alone(fp, scene):
    scene.addItem(fp.WallItem(QPointF(0, 100), QPointF(200, 100), "interior"))
    stem = fp.WallItem(QPointF(100, 130), QPointF(100, 260), "interior")  # 30" gap
    scene.addItem(stem)
    fp.rebuild_all_walls(scene)
    weld_wall_ends(scene, stem)
    assert stem.p1.y() == pytest.approx(130)             # too far -> not welded


def test_junction_outline_is_clipped_so_walls_read_solid(fp, scene):
    # crossing walls get an outline clip (their inner seams are hidden), an
    # isolated wall does not
    lone = fp.WallItem(QPointF(0, 400), QPointF(120, 400), "interior")
    scene.addItem(lone)
    scene.addItem(fp.WallItem(QPointF(0, 100), QPointF(200, 100), "interior"))
    scene.addItem(fp.WallItem(QPointF(100, 0), QPointF(100, 200), "interior"))
    fp.rebuild_all_walls(scene)
    crossing = [w for w in scene.items() if isinstance(w, fp.WallItem)
                and w is not lone]
    assert all(w._outline_clip is not None for w in crossing)  # seams hidden
    assert lone._outline_clip is None                          # nothing to clip


def _render(scene, size=200):
    """The scene rendered to a QImage, for pixel assertions."""
    from PyQt6.QtGui import QImage, QPainter
    img = QImage(size, size, QImage.Format.Format_RGB32)
    img.fill(0xFFFFFFFF)
    pr = QPainter(img)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(pr, QRectF(0, 0, size, size), QRectF(0, 0, size, size))
    pr.end()
    return img


def test_a_cross_junction_paints_with_no_seam(fp, scene):
    """THE PIXEL HALF of the junction contract (P3.4 (iv)) -- an ADDITION, not
    a rewrite: the structural guard above stays exactly as it was.

    That guard asserts the clip CACHE is populated. It would pass against a
    replacement that populated it with the WRONG clip, which is precisely what
    changing how junction neighbours are found can produce. Seam-free is an
    OUTPUT contract, so this one looks at the output.

    POLARITY, measured rather than assumed: the wall body is grey (150) and a
    seam is a DARK line across the junction interior -- the inverse of "no
    LIGHT seam pixel". So seam-free means the interior stays body-grey, and the
    `< 190` threshold from CLAUDE.md is used where it actually belongs: on the
    negative half, where an antialiased 1-px dark line reads well under 190 but
    nowhere near 100."""
    scene.addItem(fp.WallItem(QPointF(0, 100), QPointF(200, 100), "interior"))
    scene.addItem(fp.WallItem(QPointF(100, 0), QPointF(100, 200), "interior"))
    fp.rebuild_all_walls(scene)
    walls = [w for w in scene.items() if isinstance(w, fp.WallItem)]

    span = range(94, 107)                      # the junction interior
    inside = ([_render(scene).pixelColor(x, 100).red() for x in span]
              + [_render(scene).pixelColor(100, y).red() for y in span])
    body = max(inside)
    assert min(inside) >= body - 10, (
        f"a seam crosses the junction: {inside}")

    # the negative half -- without the clip the seam is really there, so the
    # assertion above can fail and is not vacuous
    for w in walls:
        w._outline_clip = None
    img = _render(scene)
    bare = [img.pixelColor(x, 100).red() for x in span]
    assert min(bare) < 190, f"expected a visible seam without the clip: {bare}"


def test_welding_closes_near_miss_junctions_and_is_idempotent(fp, scene):
    scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(300, 0), "interior"))
    scene.addItem(fp.WallItem(QPointF(150, 7), QPointF(150, 120), "interior"))
    fp.rebuild_all_walls(scene)
    weld_scene(scene)
    stem = next(w for w in scene.items() if isinstance(w, fp.WallItem)
                and abs(w.p1.x() - 150) < 1 and abs(w.p2.x() - 150) < 1)
    assert min(stem.p1.y(), stem.p2.y()) == pytest.approx(0)   # gap closed
    before = (QPointF(stem.p1), QPointF(stem.p2))
    weld_scene(scene)                                    # second sweep: no move
    assert stem.p1 == before[0] and stem.p2 == before[1]


# -- fracture-on-delete: keep room-edge stretches, drop the rest ---------------
def test_fracture_delete_free_wall_removes_whole(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    fp.rebuild_all_walls(scene)
    fp.fracture_delete_wall(scene, w)
    assert w.scene() is None
    assert not [x for x in scene.items() if isinstance(x, fp.WallItem)]


def test_fracture_delete_keeps_room_edge_drops_overhang(fp, scene, make_room):
    room = make_room(scene, 0, 0, 120, 120, "Den")
    top = next(w for w in room.walls
               if abs(w.p1.y()) < 1 and abs(w.p2.y()) < 1)
    # extend the top wall 60" past the room's right corner -> an overhang
    if top.p2.x() > top.p1.x():
        top.p2 = QPointF(180, 0)
    else:
        top.p1 = QPointF(180, 0)
    top.rebuild()
    fp.rebuild_all_walls(scene)
    edge = next(w for w in room.walls
                if abs(w.p1.y()) < 1 and abs(w.p2.y()) < 1)
    fp.fracture_delete_wall(scene, edge)
    assert room.area_sqft == pytest.approx(100.0, rel=0.05)   # 120x120 in sq ft
    kept = next(w for w in scene.items() if isinstance(w, fp.WallItem)
                and not w.is_open and abs(w.p1.y()) < 1 and abs(w.p2.y()) < 1)
    assert max(kept.p1.x(), kept.p2.x()) == pytest.approx(120, abs=1)  # no over
    assert room in kept.rooms


@pytest.mark.gui
def test_body_slide_never_snaps_an_end_to_another_wall(fp, win, drag):
    # sliding a wall's BODY must leave it parallel -- it must NOT yank an end
    # onto a nearby wall (which would tilt it)
    sc = win.scene
    a = fp.WallItem(QPointF(0, 100), QPointF(200, 100), "interior")
    b = fp.WallItem(QPointF(200, 106), QPointF(200, 260), "interior")
    sc.addItem(a)
    sc.addItem(b)
    fp.rebuild_all_walls(sc)
    win.set_tool(fp.TOOL_SELECT)
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    a.setSelected(True)
    m = win.view.transform().m11()
    # slide A down ~12"; its right end then sits ~6" from B's end (within the
    # old join tolerance) -- it must still be horizontal afterwards
    drag(win, QPointF(100, 100), 0, int(12 * m), steps=4)
    assert a.p1.y() == pytest.approx(a.p2.y())     # parallel: no snap-tilt
    assert a.p1.y() > 100                           # it did move
