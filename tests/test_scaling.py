"""P0.3 scaling harness — proves the group/bake/ungroup/rebuild hot paths scale
sub-quadratically in room count, and gives Phase 3 (P3.8) a number to beat.

Builds an n x n grid of walled, *named* rooms that share their edge walls, each
with a door, a window and two furnishings, at n=4 (16 rooms) and n=8 (64 rooms).
Times four operations and asserts each ratio t(2n)/t(n) < 8 -- sub-quadratic in
room count (a quadratic op would be ~16, since 2n has 4x the rooms).

This is by far the largest thing in the suite (the 64-room grid), so it is kept
behind @pytest.mark.slow and --quick skips it. Raw milliseconds are printed and
emitted as a warning so they surface in `pytest -ra` output; the ratios feed the
Progress log and the P3.8 comparison.
"""
import time
import warnings

import pytest

from PyQt6.QtCore import QPointF

import FloorPlanner as fp

# slow: --quick skips it. perf: CI skips it (-m "not perf") -- timing-ratio
# assertions flap on shared runners; the harness is a local gate (P0.6, P3.8).
pytestmark = [pytest.mark.slow, pytest.mark.perf]

N = 4                       # small grid is N x N; large grid is 2N x 2N
CELL = 120                  # 10 ft square rooms, sharing edge walls


def _time(fn):
    """Wall-clock milliseconds for one call of `fn`."""
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000.0


def _add_opening(room, kind, code):
    """Put one door/window at the centre of the first long-enough bound wall of
    `room` that has no opening yet."""
    for w in room.walls:
        if w.is_open or w.openings or w.length() < CELL - 12:
            continue
        try:
            op = fp.OpeningItem(w, kind, code, w.length() / 2.0)
        except ValueError:
            continue
        w.openings.append(op)
        w.rebuild()
        return


def _build_grid(win, n):
    """An n x n grid of shared-wall rooms with a door, a window and two
    furnishings each; returns the RoomItems."""
    sc = win.scene
    span = n * CELL
    off = CELL                                   # inset the grid one cell in
    # room detection floods a grid clipped to canvas_rect() (rooms.py:29), so the
    # canvas must contain the whole plan or edge cells go undetected
    fp.SETTINGS["canvas_w_in"] = span + 2 * off
    fp.SETTINGS["canvas_h_in"] = span + 2 * off
    win._apply_canvas()

    for j in range(n + 1):                       # horizontal grid lines
        sc.addItem(fp.WallItem(QPointF(off, off + j * CELL),
                               QPointF(off + span, off + j * CELL), "interior"))
    for i in range(n + 1):                       # vertical grid lines
        sc.addItem(fp.WallItem(QPointF(off + i * CELL, off),
                               QPointF(off + i * CELL, off + span), "interior"))
    fp.rebuild_all_walls(sc)

    fid = fp.furnishing_catalog()[0]["id"]
    # detect every cell against the pristine grid first (binding a room mutates
    # the shared walls, which would disturb detection of later cells)
    detected = []
    for j in range(n):
        for i in range(n):
            c = QPointF(off + i * CELL + CELL / 2, off + j * CELL + CELL / 2)
            res = fp.detect_room(sc, c)
            assert res is not None, f"cell {i},{j} not detected"
            detected.append((i, j, c, res))

    rooms = []
    for i, j, c, res in detected:
        room = fp.RoomItem(f"R{i}-{j}", c, res[0], res[1], corners=res[2])
        sc.addItem(room)
        rooms.append(room)
        sc.addItem(fp.FurnishingItem(fid, QPointF(c.x() - 24, c.y() - 24), 0))
        sc.addItem(fp.FurnishingItem(fid, QPointF(c.x() + 24, c.y() + 24), 0))
    for room in rooms:
        fp.bind_room_walls(sc, room)              # rooms own their edge walls
        _add_opening(room, "door", "3280")
        _add_opening(room, "window", "9648")
    fp.rebuild_all_walls(sc)
    return rooms


def _measure(n):
    """Build an n x n grid and time the four hot-path operations (ms)."""
    win = fp.MainWindow()
    sc = win.scene
    _build_grid(win, n)
    t = {}

    t["rebuild"] = _time(lambda: fp.rebuild_all_walls(sc))

    # select the rooms one at a time -- exactly what ctrl-clicking each room does.
    # Each setSelected fires scene.selectionChanged -> _update_edit_actions ->
    # _selected_room_shapes(), which calls bounding_walls() for every
    # already-selected room, so this is O(R^2 * W) path booleans before Ctrl+G.
    rooms = [it for it in sc.items() if isinstance(it, fp.RoomItem)]
    sc.clearSelection()

    def _select_rooms_one_at_a_time():
        for room in rooms:
            room.setSelected(True)
    t["select"] = _time(_select_rooms_one_at_a_time)

    sc.clearSelection()
    for it in sc.items():
        if isinstance(it, (fp.WallItem, fp.RoomItem, fp.FurnishingItem)):
            it.setSelected(True)
    t["group"] = _time(win.group_selected)

    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setPos(60, 60)                             # a drag...
    t["bake"] = _time(g.bake)                    # ...folded in on release

    sc.clearSelection()
    g = next(i for i in sc.items() if isinstance(i, fp.GroupItem))
    g.setSelected(True)
    t["ungroup"] = _time(win.ungroup_selected)

    win.close()
    return t


OPS = ("rebuild", "select", "group", "bake", "ungroup")


@pytest.fixture(scope="module")
def scaling():
    """Measure both grid sizes once; return raw ms and t(2n)/t(n) ratios."""
    small = _measure(N)
    large = _measure(2 * N)
    ratios = {op: large[op] / small[op] if small[op] else float("inf")
              for op in OPS}
    lines = [f"[scaling] n={N} ({N * N} rooms) -> 2n={2 * N} ({4 * N * N} rooms), "
             f"ratio threshold < 8 (quadratic ~= 16)"]
    for op in OPS:
        lines.append(f"[scaling]   {op:8s}  {small[op]:8.1f} ms -> "
                     f"{large[op]:9.1f} ms   ratio {ratios[op]:5.2f}")
    lines.append(f"[scaling] absolute: selecting all {4 * N * N} rooms one at a "
                 f"time = {large['select']:.1f} ms")
    report = "\n".join(lines)
    print("\n" + report)
    warnings.warn(UserWarning("\n" + report), stacklevel=1)   # visible in -ra
    return {"small": small, "large": large, "ratios": ratios}


def test_rebuild_scales_subquadratically(scaling):
    assert scaling["ratios"]["rebuild"] < 8


# Building the selection is the worst-scaling op (ratio ~27 at P0.3b baseline --
# beyond quadratic). Each ctrl-click fires _update_edit_actions ->
# _selected_room_shapes(), which recomputes bounding_walls() for EVERY already-
# selected room, so selecting R rooms is O(R^2 * W) path booleans. P3.5 makes
# bounding_walls trivial (stored outlines, no per-call boolean union), which
# drops the per-room constant; P3.8 is the gate that must show the ratio under 8.
# strict=False -- see the log note: the O(R^2) recompute pattern itself lives in
# _selected_room_shapes and may not fully clear until that is rewritten (P4.5).
@pytest.mark.xfail(strict=False, reason="selection build is >quadratic until P3.8")
def test_select_scales_subquadratically(scaling):
    assert scaling["ratios"]["select"] < 8


# group_selected is near-quadratic today (ratio ~13.7 at P0.3 baseline): a room's
# walls are duplicated and the whole detection engine reruns. P3.8 (vertices own
# geometry; no duplicate_wall/coalesce on group) is where this ratio drops under
# 8. strict=False so it is free to pass early (e.g. after P0.6) without flapping.
@pytest.mark.xfail(strict=False, reason="group is ~quadratic until P3.8")
def test_group_scales_subquadratically(scaling):
    assert scaling["ratios"]["group"] < 8


def test_bake_scales_subquadratically(scaling):
    assert scaling["ratios"]["bake"] < 8


# ungroup_selected is marginally super-linear today (ratio ~8.5): coalesce_all +
# rebuild over the whole plan on release. Same fix and gate as group -> P3.8.
# strict=False because the ratio hovers near the threshold run to run.
@pytest.mark.xfail(strict=False, reason="ungroup is ~quadratic until P3.8")
def test_ungroup_scales_subquadratically(scaling):
    assert scaling["ratios"]["ungroup"] < 8
