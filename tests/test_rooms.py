"""Room detection, area, inventory, naming, and region-follows-walls."""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.rooms


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


def test_room_op_needs_two_rooms(fp, win):
    r1, _ = _overlapping_rooms(fp, win)
    win._sel_order = [r1]                       # only one selected
    win.room_boolean("combine")
    assert len(_rooms(fp, win)) == 2            # unchanged, no crash


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
