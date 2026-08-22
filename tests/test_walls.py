"""Wall geometry plus door/window opening sizing and garage-door defaults."""
import pytest
from PyQt6.QtCore import QPointF, QRectF, Qt

from floorplanner.walls import merge_wall, weld_scene, weld_wall_ends
from floorplanner.vertex import Vertex

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


# -- 0070-ruling.md: a T-junction start point must land on the grid too -------
#
# nearest_wall_body_point() returns the raw geometric projection of the
# click onto the host wall's centreline, never rounded to the grid --
# _snap_start took that point VERBATIM. A fresh wall started against an
# existing wall's body silently inherited whatever fraction the click
# happened to land on, and no later operation could ever remove it (the
# bisect in 0070's own report reproduced this identically with weld/
# coalesce on and off -- the seed is the draw, not the normalisation).

def test_t_junction_start_snaps_along_the_host_wall_to_grid(fp, win):
    sc = win.scene
    host = fp.WallItem(QPointF(60, 300), QPointF(60, 420), "interior")
    sc.addItem(host)
    fp.rebuild_all_walls(sc)
    # a click near the host's body, well off any 6" line along it
    q = win.view._snap_start(QPointF(63, 359))
    assert q.x() == pytest.approx(60)              # stays exactly on the host
    assert q.y() % fp.SETTINGS["wall_snap_in"] == pytest.approx(0)


def test_t_junction_start_on_a_diagonal_host_is_unchanged(fp, win):
    """A diagonal host has no single well-defined grid position along it,
    so the point is returned as the raw projection -- same as before this
    fix, not a regression for the deliberate-diagonal case."""
    sc = win.scene
    host = fp.WallItem(QPointF(0, 0), QPointF(200, 200), "interior")
    sc.addItem(host)
    fp.rebuild_all_walls(sc)
    q = win.view._snap_start(QPointF(101, 99))
    assert q.x() == pytest.approx(q.y())            # still exactly on y=x


def test_w7offgrid_macro_lands_every_vertex_on_the_snap_grid(fp, win):
    """0070-ruling.md: Patrick's own reproduced report, replayed verbatim.
    This is about what the app PRODUCES, not the corpus of legitimately
    off-grid loaded history (0070 sec5 item 3) -- a fresh scene, the macro
    the only input, every vertex it creates must land on the snap grid."""
    import pathlib
    macro = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "w7offgrid.fpm"
    for line in macro.read_text(encoding="utf-8").splitlines():
        if line.strip():
            res = win.run_macro(line)
            assert res["ok"], res
    step = fp.SETTINGS["wall_snap_in"]
    walls = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    assert len(walls) == 9, f"wall count {len(walls)} after the replay"
    for w in walls:
        for label, v in (("p1.x", w.p1.x()), ("p1.y", w.p1.y()),
                          ("p2.x", w.p2.x()), ("p2.y", w.p2.y())):
            r = v % step
            assert r < 1e-6 or step - r < 1e-6, (
                f"wall {w.uid} {label}={v} is not on the {step}\" grid")


def test_wall_uid_is_lazy_stable_and_distinct(fp, scene):
    """`WallItem.uid` mirrors `Vertex.uid` exactly (vertex.py's own module
    note): minted on first read, then fixed for the item's lifetime -- a
    session-local identity for the status bar, not the id a saved document
    assigns (that renumbers geometrically at export)."""
    a = fp.WallItem(QPointF(0, 0), QPointF(100, 0), "interior")
    b = fp.WallItem(QPointF(0, 50), QPointF(100, 50), "interior")
    scene.addItem(a)
    scene.addItem(b)
    assert a.uid.startswith("W") and b.uid.startswith("W")
    assert a.uid != b.uid
    assert a.uid == a.uid                  # stable across repeated reads


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


# -- delete is deletion (P4.1): the wall goes whole; a bordering room survives
# via its stored outline, the vacated edge open. These two INTENTIONALLY
# replace the fracture-on-delete pair that encoded the old trim-and-rebind
# semantics (see the P4.1 task text and Progress log entry).
def test_delete_free_wall_removes_whole(fp, scene):
    w = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    scene.addItem(w)
    fp.rebuild_all_walls(scene)
    fp.delete_wall(scene, w)
    assert w.scene() is None
    assert not [x for x in scene.items() if isinstance(x, fp.WallItem)]


def test_delete_overhanging_wall_goes_whole_room_keeps_area(fp, scene, make_room):
    room = make_room(scene, 0, 0, 120, 120, "Den")
    top = next(w for w in room.walls
               if abs(w.p1.y()) < 1 and abs(w.p2.y()) < 1)
    # extend the top wall 60" past the room's right corner -> an overhang
    # DETACH the end past the corner: the room's outline must stay at 120, so
    # this is a fresh vertex, not a relocation of the shared corner.
    attr = "p2" if top.p2.x() > top.p1.x() else "p1"
    top.set_end_vertex(attr, Vertex.at(QPointF(180, 0)))
    top.rebuild()
    fp.rebuild_all_walls(scene)
    edge = next(w for w in room.walls
                if abs(w.p1.y()) < 1 and abs(w.p2.y()) < 1)
    fp.delete_wall(scene, edge)
    # P4.1: no trimmed survivor is minted -- the wall is genuinely gone and
    # the room keeps its area through its stored outline, the edge now open
    assert edge.scene() is None
    assert not [w for w in scene.items() if isinstance(w, fp.WallItem)
                and abs(w.p1.y()) < 1 and abs(w.p2.y()) < 1]
    assert room.area_sqft == pytest.approx(100.0, rel=0.05)   # 120x120 in sq ft
    assert len(room.open_edges()) == 1
    assert len(room.walls) == 3


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


# -- defect 25 (P4.1b): a wall end landing inside a doorway says so AT THE
# GESTURE, naming the doorway -- not the later generic torn-network line.
# Both tests assert through the public surface (the status bar after the
# debounce drain) so they run unchanged against pre-fix code, where they fail
# on the message assert: that run is the fail-first receipt.
def _host_with_door(fp, sc):
    host = fp.WallItem(QPointF(0, 0), QPointF(240, 0), "interior")
    sc.addItem(host)
    door = fp.OpeningItem(host, "door", "3280", 120.0)   # spans 104..136
    host.openings.append(door)
    fp.rebuild_all_walls(sc)
    return host


@pytest.mark.gui
def test_drawing_a_wall_into_a_doorway_names_the_doorway_at_release(
        fp, win, drag):
    # the Gate-3 scenario: draw a wall whose end lands on the host's body
    # inside the door; the join correctly declines to split through it, so
    # the end stays unwelded -- and the gesture must say so, naming the door
    sc = win.scene
    host = _host_with_door(fp, sc)
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    win.set_tool(fp.TOOL_WALL_INT)
    m = win.view.transform().m11()
    drag(win, QPointF(120, 96), 0, -int(96 * m), steps=4)
    drawn = next(w for w in sc.items() if isinstance(w, fp.WallItem)
                 and w is not host and abs(w.p1.x() - 120) < 6)
    end = min((drawn.p1, drawn.p2), key=lambda p: abs(p.y()))
    # precondition (the defect-28 lesson): the gesture really made the state
    # -- the drawn end rests ON the host's centreline, inside the door span
    assert abs(end.y()) < 1.0 and 104 < end.x() < 136
    win._commit_if_changed()
    msg = win.statusBar().currentMessage()
    assert "door 3280" in msg, f"gesture said nothing specific: {msg!r}"
    assert "drawing a wall" in msg


@pytest.mark.gui
def test_dragging_an_end_into_a_doorway_names_the_doorway_at_release(
        fp, win, drag):
    sc = win.scene
    _host_with_door(fp, sc)
    w = fp.WallItem(QPointF(120, 60), QPointF(120, 180), "interior")
    sc.addItem(w)
    fp.rebuild_all_walls(sc)
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    win.set_tool(fp.TOOL_SELECT)
    w.setSelected(True)
    m = win.view.transform().m11()
    # grab the free end at (120, 60) and drag it down onto the door
    drag(win, QPointF(120, 60), 0, -int(60 * m), steps=4)
    end = min((w.p1, w.p2), key=lambda p: abs(p.y()))
    assert abs(end.y()) < 1.0 and 104 < end.x() < 136   # precondition
    win._commit_if_changed()
    msg = win.statusBar().currentMessage()
    assert "door 3280" in msg, f"gesture said nothing specific: {msg!r}"
    assert "dragging a wall end" in msg


# -- ruling 2 (P4.3): the tiered doorway policy ------------------------------
# Tier 1: a jamb within the gesture's JOIN_TOL of the landing point takes the
# end (snap-to-jamb, the junction the user meant). Tier 2: no jamb in
# tolerance -> land-unwelded-and-report (the P4.1b message above, unchanged --
# its landing at x=120 sits 16" from either jamb, outside the tolerance).
# Never split, never refuse. auto_weld's decision: with it off, or under
# shuffle, no weld is attempted and the message stays quiet.
@pytest.mark.gui
def test_a_drawn_end_near_a_jamb_snaps_to_it(fp, win, drag):
    sc = win.scene
    host = _host_with_door(fp, sc)          # door 3280 spans 104..136
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    win.set_tool(fp.TOOL_WALL_INT)
    m = win.view.transform().m11()
    # drawn to rest at x=108: inside the span, 4" from the jamb at 104
    drag(win, QPointF(108, 96), 0, -int(96 * m), steps=4)
    drawn = next(w for w in sc.items() if isinstance(w, fp.WallItem)
                 and w is not host and abs(max(w.p1.y(), w.p2.y()) - 96) < 6)
    end = min((drawn.p1, drawn.p2), key=lambda p: abs(p.y()))
    assert abs(end.y()) < 1.0               # precondition: really landed
    assert end.x() == pytest.approx(104.0, abs=0.1), (
        "the end must snap to the jamb, not rest inside the doorway")
    win._commit_if_changed()
    assert "door 3280" not in win.statusBar().currentMessage(), (
        "a snapped landing has nothing to report")


@pytest.mark.gui
def test_a_dragged_end_near_a_jamb_snaps_to_it(fp, win, drag):
    sc = win.scene
    _host_with_door(fp, sc)
    w = fp.WallItem(QPointF(108, 60), QPointF(108, 180), "interior")
    sc.addItem(w)
    fp.rebuild_all_walls(sc)
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    win.set_tool(fp.TOOL_SELECT)
    w.setSelected(True)
    m = win.view.transform().m11()
    drag(win, QPointF(108, 60), 0, -int(60 * m), steps=4)
    end = min((w.p1, w.p2), key=lambda p: abs(p.y()))
    assert abs(end.y()) < 1.0               # precondition: really landed
    assert end.x() == pytest.approx(104.0, abs=0.1), (
        "the dragged end must snap to the jamb -- the ruling's deliberate, "
        "narrow exception to 'left exactly where the drag put it'")
    win._commit_if_changed()
    assert "door 3280" not in win.statusBar().currentMessage()


@pytest.mark.gui
def test_auto_weld_off_leaves_the_end_alone_and_says_nothing(fp, win, drag):
    sc = win.scene
    _host_with_door(fp, sc)
    fp.SETTINGS["auto_weld"] = False
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    win.set_tool(fp.TOOL_WALL_INT)
    m = win.view.transform().m11()
    drag(win, QPointF(108, 96), 0, -int(96 * m), steps=4)
    drawn = next(w for w in sc.items() if isinstance(w, fp.WallItem)
                 and abs(max(w.p1.y(), w.p2.y()) - 96) < 6)
    end = min((drawn.p1, drawn.p2), key=lambda p: abs(p.y()))
    assert abs(end.y()) < 1.0               # precondition: really landed
    assert end.x() == pytest.approx(108.0, abs=0.1), (
        "with auto_weld off NO weld pass runs -- no jamb snap either")
    win._commit_if_changed()
    assert "door 3280" not in win.statusBar().currentMessage(), (
        "no weld attempted -> no policy question -> no message")


@pytest.mark.gui
def test_shuffle_suppresses_the_doorway_message(fp, win, drag):
    # the P4.1b geometry VERBATIM (landing at 120, deep inside the door),
    # under shuffle: an unwelded end is the mode's intended state, and
    # warning about it would be nagging the mode for working
    sc = win.scene
    _host_with_door(fp, sc)
    fp.SETTINGS["shuffle"] = True
    win.resize(1100, 900)
    win.show()
    win.zoom_fit()
    win.set_tool(fp.TOOL_WALL_INT)
    m = win.view.transform().m11()
    drag(win, QPointF(120, 96), 0, -int(96 * m), steps=4)
    drawn = next(w for w in sc.items() if isinstance(w, fp.WallItem)
                 and abs(max(w.p1.y(), w.p2.y()) - 96) < 6)
    end = min((drawn.p1, drawn.p2), key=lambda p: abs(p.y()))
    assert abs(end.y()) < 1.0 and 104 < end.x() < 136   # precondition
    win._commit_if_changed()
    assert "door 3280" not in win.statusBar().currentMessage()


# -- defect 34 (P4.2): the gap REVIEW -- list, never auto-close ---------------
def _gap_doc(win):
    import warnings
    from floorplanner.design.bridge import design_from_scene
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return design_from_scene(win).to_dict()


def test_near_vertex_gaps_lists_the_band_and_only_the_band(fp, win):
    from floorplanner.design.validate import near_vertex_gaps
    sc = win.scene
    # a 1.5" gap (probably a mistake) and a 6" gap (probably a reveal):
    # BOTH listed with distances -- the review reports, a human decides
    fp.rebuild_all_walls(sc)
    sc.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(121.5, 0), QPointF(240, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(0, 60), QPointF(120, 60), "interior"))
    sc.addItem(fp.WallItem(QPointF(126, 60), QPointF(240, 60), "interior"))
    # welded corners (0.0") and honestly-apart ends (>= 9") must NOT list
    fp.rebuild_all_walls(sc)
    gaps = near_vertex_gaps(_gap_doc(win))
    dists = sorted(round(g[3], 2) for g in gaps)
    assert dists == [1.5, 6.0], f"listed {dists}"


def test_close_gap_welds_one_pair_and_leaves_the_reveal(fp, win):
    from floorplanner.design.validate import near_vertex_gaps
    sc = win.scene
    sc.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(121.5, 0), QPointF(240, 0), "interior"))
    sc.addItem(fp.WallItem(QPointF(0, 60), QPointF(120, 60), "interior"))
    sc.addItem(fp.WallItem(QPointF(126, 60), QPointF(240, 60), "interior"))
    fp.rebuild_all_walls(sc)
    gaps = near_vertex_gaps(_gap_doc(win))
    assert len(gaps) == 2
    lvl, a, b, dist = gaps[0]                     # nearest first: the 1.5"
    assert dist == pytest.approx(1.5)
    n = fp.close_gap(sc, QPointF(*a), QPointF(*b))
    assert n >= 1                                 # something really welded
    left = near_vertex_gaps(_gap_doc(win))
    dists = [round(g[3], 2) for g in left]
    assert dists == [6.0], f"after closing the 1.5\": {dists}"
    # the closed pair is ONE corner now, at the kept point `a`
    ends = [w.end_vertex(attr) for w in sc.items()
            if isinstance(w, fp.WallItem) and abs(w.p1.y()) < 1
            for attr in ("p1", "p2")]
    at_a = [v for v in ends
            if abs(v.x - a[0]) < 0.01 and abs(v.y - a[1]) < 0.01]
    assert len(at_a) == 2 and at_a[0] is at_a[1]  # same Vertex object
    # and the deliberate 6" reveal is exactly where the user drew it
    reveal = next(w for w in sc.items() if isinstance(w, fp.WallItem)
                  and abs(w.p1.y() - 60) < 1 and w.p1.x() > 120)
    assert min(reveal.p1.x(), reveal.p2.x()) == pytest.approx(126)


def test_floating_room_distance_is_not_a_gap(fp, win):
    from floorplanner.design.validate import near_vertex_gaps
    from floorplanner.extract import extract_room
    sc = win.scene
    corners = [QPointF(0, 0), QPointF(120, 0), QPointF(120, 120),
               QPointF(0, 120)]
    for i in range(4):
        sc.addItem(fp.WallItem(corners[i], corners[(i + 1) % 4], "interior"))
    fp.rebuild_all_walls(sc)
    res = fp.detect_room(sc, QPointF(60, 60))
    room = fp.RoomItem("Den", QPointF(60, 60), res[0], res[1], corners=res[2])
    sc.addItem(room)
    fp.bind_room_walls(sc, room)
    sc.addItem(fp.WallItem(QPointF(200, 0), QPointF(200, 120), "interior"))
    fp.rebuild_all_walls(sc)
    extract_room(sc, room)
    room._translate(78, 0)     # park the floating room 2" from the lone wall
    gaps = near_vertex_gaps(_gap_doc(win))
    assert gaps == [], f"a floating room's position listed as a gap: {gaps}"


def test_close_gap_leaves_outlines_holding_their_walls_corners(fp, win,
                                                               make_room):
    # Found at the P4.2 mini-gate (second finding): close the review's gaps,
    # then drag a wall -- M Bath / Hall / Lounge drew dashed DIAGONALS to
    # corners their walls no longer held. Root cause: close_gap folded WALL
    # ends onto one anchor vertex but left the OUTLINES holding coincident-
    # but-distinct twins (the P3.5 invariant broken); the next drag moved the
    # walls' vertex and stranded the outline corners. The invariant is
    # asserted directly: after closing, every outline corner IS one of its
    # room's wall-end vertices, by identity.
    from floorplanner.design.validate import near_vertex_gaps
    sc = win.scene
    ra = make_room(sc, 0, 0, 120, 120, "A")
    rb = make_room(sc, 121.5, 0, 120, 120, "B")
    gaps = near_vertex_gaps(_gap_doc(win))
    assert len(gaps) == 2, f"precondition: two 1.5\" pairs, got {gaps}"
    for _lvl, a, b, _dist in list(gaps):
        assert fp.close_gap(sc, QPointF(*a), QPointF(*b)) >= 1
    assert near_vertex_gaps(_gap_doc(win)) == []
    for room in (ra, rb):
        ends = {id(w.end_vertex(at)) for w in room.walls
                for at in ("p1", "p2")}
        for e in room.outline:
            assert id(e.v) in ends, (
                f"{room.name}: outline corner at ({e.v.x:.1f}, {e.v.y:.1f}) "
                f"is not one of its walls' corners -- the next drag strands "
                f"it into a diagonal")
