"""P0.4 characterization tests — pin down what the app does TODAY, so the
Phase 3/4 rewrites are measured against real current behaviour rather than
assumptions. Tests that fail today are marked xfail with the phase that flips
them; each such xfail is a promise the migration must keep.

No existing test is modified by this file.
"""
import pytest
from PyQt6.QtCore import QPointF

import FloorPlanner as fp

pytestmark = pytest.mark.groups


# --------------------------------------------------------------------------
# builders
# --------------------------------------------------------------------------
def _add_opening(room, kind, code, min_len):
    """Put one door/window on the first bound wall long enough and not yet
    opened; return the OpeningItem."""
    for w in room.walls:
        if w.openings or w.length() < min_len:
            continue
        op = fp.OpeningItem(w, kind, code, w.length() / 2.0)
        w.openings.append(op)
        w.rebuild()
        return op
    raise AssertionError("no wall available for opening")


def _furnished_room(win, make_room, fid, name="Den"):
    """A named 144x120 room with a door, a window and two furnishings inside.
    Returns (room, [door, window], [furn, furn])."""
    sc = win.scene
    room = make_room(sc, 0, 0, 144, 120, name)
    door = _add_opening(room, "door", "3280", 44)
    window = _add_opening(room, "window", "9648", 108)
    furns = [fp.FurnishingItem(fid, QPointF(48, 48), 0),
             fp.FurnishingItem(fid, QPointF(96, 72), 0)]
    for f in furns:
        sc.addItem(f)
    fp.rebuild_all_walls(sc)
    return room, [door, window], furns


def _group(win, items):
    sc = win.scene
    sc.clearSelection()
    for it in items:
        it.setSelected(True)
    win.group_selected()
    return next(i for i in sc.items() if isinstance(i, fp.GroupItem))


def _counts(sc):
    walls = [w for w in sc.items() if isinstance(w, fp.WallItem)]
    return (len(walls), sum(len(w.openings) for w in walls))


# --------------------------------------------------------------------------
# 1. openings ride a grouped room rigidly (move, then rotate)
# --------------------------------------------------------------------------
def test_group_move_preserves_opening_s(win, make_room, first_furnishing):
    room, ops, furns = _furnished_room(win, make_room, first_furnishing)
    before = {id(op): op.s for op in ops}
    g = _group(win, [room, *room.walls, *furns])
    g.setPos(240, 180)
    g.bake()
    for op in ops:
        assert op.s == pytest.approx(before[id(op)], abs=0.5), \
            "opening slid along its wall on move"


def test_group_rotate_preserves_opening_s(win, make_room, first_furnishing):
    room, ops, furns = _furnished_room(win, make_room, first_furnishing)
    before = {id(op): op.s for op in ops}
    g = _group(win, [room, *room.walls, *furns])
    c = g.childrenBoundingRect().center()
    g._begin_rotation(QPointF(c.x() + 100, c.y()))
    g._apply_rotation(QPointF(c.x(), c.y() + 100), False)   # +90 deg
    g._finish_rotation()
    for op in ops:
        assert op.s == pytest.approx(before[id(op)], abs=0.5), \
            "opening slid along its wall on rotation"


# --------------------------------------------------------------------------
# 2. deleting one wall of a room -- split into 2a/2b (P4.1).
# One test cannot distinguish today's behaviour from P4.1's: the room survives
# today ONLY because the wall is never actually deleted. fracture_delete_wall
# (walls.py:300-354) keeps every stretch running along a room perimeter and
# rebinds it, so deleting a room's own perimeter wall is silently a no-op --
# measured at P0.4: 4 walls in, 4 walls out, 0 open edges (defect 17: the user
# presses Delete and nothing happens, with no message). Under P4.1 the wall
# genuinely goes and the edge becomes `wall: null`. So:
#   2a asserts the durable invariant (room survives) -- passes today, hard.
#   2b asserts the wall is actually gone -- xfail until P4.1.
# --------------------------------------------------------------------------
def _delete_a_room_wall(win, make_room, fid):
    """Build a furnished room, delete one built perimeter wall; return
    (scene, room_name, room_area, furnishings)."""
    sc = win.scene
    room, ops, furns = _furnished_room(win, make_room, fid)
    name, area = room.name, room.area_sqft
    wall = next(iter(room.walls))
    sc.clearSelection()
    wall.setSelected(True)
    win.delete_selected()
    return sc, name, area, furns


def test_delete_wall_keeps_room(win, make_room, first_furnishing):
    # asserts only the invariant, NOT the wall count, so it stays valid when
    # P4.1 changes the mechanism (wall removed; room persists via stored outline)
    sc, name, area, furns = _delete_a_room_wall(win, make_room, first_furnishing)
    rooms = [r for r in sc.items() if isinstance(r, fp.RoomItem)]
    assert any(r.name == name for r in rooms), "room gone after deleting a wall"
    r = next(r for r in rooms if r.name == name)
    assert r.area_sqft == pytest.approx(area, rel=0.02), "room area changed"
    assert all(f.scene() is sc for f in furns), "furnishings lost"


@pytest.mark.xfail(reason="delete is a no-op on a room's own wall until P4.1 "
                          "(defect 17)", strict=False)
def test_delete_wall_actually_removes_the_wall(win, make_room, first_furnishing):
    # under P4.1 the deleted wall is really gone: the room keeps 3 built walls
    # and 1 open (wall: null) edge, not the 4 built walls it has today
    sc, name, _area, _furns = _delete_a_room_wall(win, make_room, first_furnishing)
    room = next(r for r in sc.items()
                if isinstance(r, fp.RoomItem) and r.name == name)
    built = len(room.walls)
    openn = len(room.open_edges())
    assert built == 3 and openn == 1, \
        f"delete was a no-op: {built} built walls, {openn} open edges"


# --------------------------------------------------------------------------
# 3. a group survives serialize -> load_data  (P4.5)
# --------------------------------------------------------------------------
@pytest.mark.xfail(reason="groups do not serialize until P4.5 (defect 3)",
                   strict=False)
def test_group_survives_roundtrip(win, make_room, first_furnishing):
    sc = win.scene
    r1 = make_room(sc, 0, 0, 120, 96, "Room 1")
    r2 = make_room(sc, 200, 0, 120, 96, "Room 2")
    _group(win, [r1, r2, *r1.walls, *r2.walls])
    data = win.serialize()
    win.load_data(data)
    assert any(isinstance(i, fp.GroupItem) for i in win.scene.items()), \
        "group did not survive the round-trip"


# --------------------------------------------------------------------------
# 4. group + move, then undo, returns to the pre-group state
# Promoted to a HARD PASS at P0.5: fix 2 (project_from_scene copies room
# properties) closed this -- the pre-group serialize() snapshot no longer
# aliases the live properties dict, so group+move can't corrupt it and undo
# compares equal. This is a durable invariant (the plan must revert) and must
# not regress. P4.5's other half -- the group itself surviving save/load/redo --
# is still held by test 3 (test_group_survives_roundtrip), which stays xfail.
# --------------------------------------------------------------------------
def test_group_move_undo_restores(win, make_room, first_furnishing):
    # P2.3 moved the yardstick from serialize() to snapshot(). serialize() is
    # now only the legacy v4 exporter, and it reports PRESENTATION detail the
    # canonical document deliberately quotients away: after an undo this room's
    # perimeter_corners come back rotated to start at the least corner -- the
    # same polygon, a different first element. Comparing v4 dicts would fail on
    # that and prove nothing. The plan is the canonical document, so compare it,
    # and assert the polygon separately so a REAL geometry change still fails.
    room, ops, furns = _furnished_room(win, make_room, first_furnishing)
    win._reset_undo()
    before = win.snapshot()
    before_poly = {r.name: {(round(c.x(), 3), round(c.y(), 3))
                            for c in (r.corners or [])}
                   for r in win.scene.items() if isinstance(r, fp.RoomItem)}
    g = _group(win, [room, *room.walls, *furns])
    g.setPos(180, 120)
    g.bake()
    win.undo()
    assert win.snapshot() == before, "undo did not restore the pre-group plan"
    after_poly = {r.name: {(round(c.x(), 3), round(c.y(), 3))
                           for c in (r.corners or [])}
                  for r in win.scene.items() if isinstance(r, fp.RoomItem)}
    assert after_poly == before_poly, "the room polygon itself changed"


# --------------------------------------------------------------------------
# 5. grouped walls are exempt from the merge sweep (the group() is None gate)
# --------------------------------------------------------------------------
def test_grouped_walls_exempt_from_coalesce(win, make_room, first_furnishing):
    sc = win.scene
    room, ops, furns = _furnished_room(win, make_room, first_furnishing)
    g = _group(win, [room, *room.walls, *furns])
    grouped = [w for w in g.childItems() if isinstance(w, fp.WallItem)]
    n_grouped = len(grouped)
    # a free wall coincident with one of the grouped walls
    gw = grouped[0]
    free = fp.WallItem(QPointF(gw.p1), QPointF(gw.p2), gw.wall_type)
    sc.addItem(free)
    fp.merge_all(sc)
    still_grouped = [w for w in g.childItems() if isinstance(w, fp.WallItem)]
    assert len(still_grouped) == n_grouped, "the merge sweep ate a grouped wall"
    assert all(w.group() is g for w in still_grouped)


# --------------------------------------------------------------------------
# 6. group/ungroup 4x reaches a fixed point in wall + opening counts
#    (promoted from the deleted test_zzleak.py)
# --------------------------------------------------------------------------
def test_group_ungroup_reaches_fixed_point(win, make_room, first_furnishing):
    sc = win.scene
    room, ops, furns = _furnished_room(win, make_room, first_furnishing)
    counts = []
    for _ in range(4):
        room = next(r for r in sc.items() if isinstance(r, fp.RoomItem))
        g = _group(win, [room, *room.walls, *furns])
        g.setPos(48, 0)
        g.bake()
        sc.clearSelection()
        g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
        g.setSelected(True)
        win.ungroup_selected()
        counts.append(_counts(sc))
    assert counts[1:] == counts[:-1], f"no fixed point: {counts}"
