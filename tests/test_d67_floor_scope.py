"""D67 -- selection is not scoped to the active floor: the two measured sites.

The rule D67 gives the fix: VISIBILITY AND PERMISSION ARE SEPARATE GRANTS --
an inactive floor may be drawn; it may not be hit-tested, selected, banded
or dragged. Every selection route measured clean (0201-report.md sec1);
the leaks were two lookups that take geometry without asking its floor:

  * `RoomItem.interior_walls()` -- `group_selected` adds it for a selected
    room, so a group made on the upper floor took two lower-floor partition
    walls that stand under the room in plan, and the drag moved both floors
    (0201 sec1, on `examples/roundedMultifloor.json`).
  * `_place_opening` -- the Door/Window tool took the first wall under the
    cursor, so a click on a lower-only wall from the upper level cut an
    opening into the lower level (0202-report.md sec4, on
    `fixtures/wiscaway-2level-stacked-floor.json`).

Both tests are the probes' own gestures, and both were RED before the
predicate went in.
"""
import pathlib

import pytest
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtWidgets import QInputDialog

from floorplanner.rooms import room_walls

pytestmark = pytest.mark.groups

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _by_floor(items):
    out = {}
    for it in items:
        f = getattr(it, "floor", None)
        if f is None and hasattr(it, "wall"):
            f = it.wall.floor
        out[f] = out.get(f, 0) + 1
    return out


def _open(win, plan, floor, show_others):
    win.prepare_headless()
    win.load_path(str(ROOT / plan))
    win.show_other_floors = show_others
    win.switch_floor(floor)
    win._sync_floor_state()


@pytest.mark.parametrize("show_others", [False, True])
def test_a_rooms_interior_walls_are_its_own_floors(fp, win, show_others):
    _open(win, "examples/roundedMultifloor.json", "second", show_others)
    rooms = [r for r in win.scene.items() if isinstance(r, fp.RoomItem) and r.floor == "second"]
    assert rooms
    leaks = {(r.name, w.floor) for r in rooms
             for w in room_walls(r) + r.interior_walls()
             if isinstance(w, fp.WallItem) and w.floor != r.floor}
    assert leaks == set()
    # the positive control: the lower partition that leaked, rebuilt as a
    # wall of the room's OWN floor at the same place, IS an interior wall
    # -- the predicate removed the other floor's walls, not the answer
    room, leaked = next(
        (r, w) for r in rooms
        for w in win.scene.items()
        if isinstance(w, fp.WallItem) and w.floor == "default"
        and not w._hit.intersects(r._boundary_band())
        and r.path.contains(w.p1) and r.path.contains(w.p2))
    own = fp.WallItem(QPointF(leaked.p1), QPointF(leaked.p2), leaked.wall_type)
    win.scene.addItem(own)
    fp.rebuild_all_walls(win.scene)
    assert own.floor == "second"
    assert own in room.interior_walls() and leaked not in room.interior_walls()


@pytest.mark.parametrize("show_others", [False, True])
def test_a_group_made_on_the_upper_floor_holds_nothing_of_the_lower(fp, win, show_others):
    """0201 sec1's gesture: band the whole plan on the second floor, group,
    drag. The group was `{'default': 2, 'second': 41}`; the drag moved
    three lower-floor vertices and everything holding them."""
    _open(win, "examples/roundedMultifloor.json", "second", show_others)
    lower_before = sorted(
        (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y())
        for w in win.scene.items() if isinstance(w, fp.WallItem) and w.floor == "default")
    assert lower_before, "the plan has a lower floor to protect"
    win.view.select_in_rect(QRectF(600.0, 0.0, 1200.0, 1200.0))
    assert set(_by_floor(win.scene.selectedItems())) == {"second"}
    win.group_selected()
    groups = [g for g in win.scene.items() if isinstance(g, fp.GroupItem)]
    assert len(groups) == 1
    members = _by_floor(groups[0].childItems())
    assert set(members) == {"second"}, members
    assert members["second"] > 30, "the group is not empty"
    w2 = next(w for w in win.scene.items() if isinstance(w, fp.WallItem) and w.floor == "second")
    m = QPointF((w2.p1.x() + w2.p2.x()) / 2, (w2.p1.y() + w2.p2.y()) / 2)
    res = win.run_macro(f"S CLICK {m.x():.0f} {m.y():.0f} DRAG {m.x() + 60:.0f} {m.y() + 36:.0f}")
    assert res["ok"], res
    lower_after = sorted(
        (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y())
        for w in win.scene.items() if isinstance(w, fp.WallItem) and w.floor == "default")
    assert lower_after == lower_before, "the drag moved the lower floor"


def _lonely_lower_wall_point(fp, win, lower, upper):
    """The midpoint of a lower wall with no upper wall under the cursor."""
    walls = sorted((w for w in win.scene.items() if isinstance(w, fp.WallItem) and w.floor == lower),
                   key=lambda w: -w.length())
    for w in walls:
        m = QPointF((w.p1.x() + w.p2.x()) / 2.0, (w.p1.y() + w.p2.y()) / 2.0)
        hit = win.scene.items(m)
        if w in hit and not any(isinstance(it, fp.WallItem) and it.floor == upper for it in hit):
            return w, m
    return None, None


def _openings(fp, win, floor):
    return sum(1 for it in win.scene.items() if isinstance(it, fp.OpeningItem)
               and it.wall.floor == floor)


def test_the_door_tool_does_not_cut_another_levels_ghosted_wall(fp, win, monkeypatch):
    """0202 sec4: from the upper level with other floors shown, a Door-tool
    click on a lower-only wall took the lower level's openings 56 -> 57."""
    monkeypatch.setattr(QInputDialog, "getText",
                        staticmethod(lambda *a, **k: (k.get("text", "3280"), True)))
    _open(win, "fixtures/wiscaway-2level-stacked-floor.json", "upper", True)
    lw, m = _lonely_lower_wall_point(fp, win, "default", "upper")
    assert lw is not None, "the fixture has a lower-only wall under the cursor"
    before = (_openings(fp, win, "default"), _openings(fp, win, "upper"))
    assert before[0] > 0
    win.set_tool(fp.TOOL_DOOR)
    win.view._place_opening(m, "door")
    assert (_openings(fp, win, "default"), _openings(fp, win, "upper")) == before
    assert "wall" in win.statusBar().currentMessage().lower()


def test_the_door_tool_still_cuts_a_wall_of_the_active_level(fp, win, monkeypatch):
    """The positive control for the test above: the same tool, a wall of
    the active level, one more opening on that level and none elsewhere."""
    monkeypatch.setattr(QInputDialog, "getText",
                        staticmethod(lambda *a, **k: (k.get("text", "3280"), True)))
    _open(win, "fixtures/wiscaway-2level-stacked-floor.json", "upper", True)
    uw, m = _lonely_lower_wall_point(fp, win, "upper", "default")
    assert uw is not None
    before = (_openings(fp, win, "default"), _openings(fp, win, "upper"))
    win.set_tool(fp.TOOL_DOOR)
    win.view._place_opening(m, "door")
    assert (_openings(fp, win, "default"), _openings(fp, win, "upper")) == (before[0], before[1] + 1)
