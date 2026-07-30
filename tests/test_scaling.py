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
from PyQt6.QtWidgets import QApplication

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

    # P2.3: the undo snapshot is now the canonical v5 document, so a settled
    # edit walks the whole scene. Measured here so P6.1 -- "undo cost is
    # independent of plan size" -- has a baseline to be measured against, and so
    # a regression in the walk shows up as an undo stall rather than a mystery.
    win._reset_undo()
    t["snapshot"] = _time(win.snapshot)
    fp.rebuild_all_walls(sc)
    win._commit_if_changed()                     # one undoable step to revert
    rooms0 = sum(1 for it in sc.items() if isinstance(it, fp.RoomItem))
    it0 = next(it for it in sc.items() if isinstance(it, fp.FurnishingItem))
    it0.setPos(it0.pos() + QPointF(6, 6))
    win._commit_if_changed()
    t["undo"] = _time(win.undo)
    assert sum(1 for it in sc.items()
               if isinstance(it, fp.RoomItem)) == rooms0,         "undo lost rooms on the grid"

    # Two selection paths with genuinely different costs (P0.6 amendment):
    rooms = [it for it in sc.items() if isinstance(it, fp.RoomItem)]
    app = QApplication.instance()

    # select_burst: select all rooms one at a time WITHOUT pumping the event loop
    # -- Ctrl+A, rubber-band, the macro runner. The selectionChanged burst arrives
    # faster than the debounce, so the enable/disable pass runs once, later. The
    # DEBOUNCE (P0.6 item 1 fix a) is what makes this cheap.
    sc.clearSelection()

    def _select_burst():
        for room in rooms:
            room.setSelected(True)
    t["select_burst"] = _time(_select_burst)

    # select_interactive: processEvents after EACH setSelected -- a human ctrl-
    # clicking, far slower than the timer, so _apply_edit_actions fires once per
    # click and the debounce buys nothing. The CHEAP-COUNT fix (P0.6 item 1 fix b)
    # is what makes this cheap; it is the honest model of the reported stall.
    sc.clearSelection()

    def _select_interactive():
        for room in rooms:
            room.setSelected(True)
            app.processEvents()
    t["select_interactive"] = _time(_select_interactive)

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

    # DEFECT 28: `win.close()` hides a window and leaves its 180 ms dirty timer
    # running. These two windows are built by a MODULE-scoped fixture, so they
    # predate every per-test disposal and would outlive the whole file --
    # exactly the leak the conftest guard exists to catch, and it caught these.
    from conftest import dispose_window
    dispose_window(win)
    return t


OPS = ("rebuild", "snapshot", "undo", "select_burst", "select_interactive",
       "group", "bake", "ungroup")


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
        lines.append(f"[scaling]   {op:18s}  {small[op]:8.1f} ms -> "
                     f"{large[op]:9.1f} ms   ratio {ratios[op]:5.2f}")
    lines.append(f"[scaling] absolute (all {4 * N * N} rooms one at a time): "
                 f"burst {large['select_burst']:.1f} ms, "
                 f"interactive {large['select_interactive']:.1f} ms")
    report = "\n".join(lines)
    print("\n" + report)
    warnings.warn(UserWarning("\n" + report), stacklevel=1)   # visible in -ra
    return {"small": small, "large": large, "ratios": ratios}


def test_rebuild_scales_subquadratically(scaling):
    assert scaling["ratios"]["rebuild"] < 8


# Selection-building was the worst-scaling op (ratio ~27 at P0.3b -- beyond
# quadratic): each setSelected fired _selected_room_shapes(), O(R^2 * W) path
# booleans. P0.6 item 1 fixed it two ways; the two user paths are measured apart.
# select_burst: Ctrl+A / rubber-band / macro. The debounce coalesces the burst,
# so the harness (no event pump) measures the deferral -- ~1 ms at 64 rooms.
# ASSERT THE ABSOLUTE, NOT THE RATIO: the numbers here (0.2 ms -> 1.1 ms) sit at
# the perf_counter floor, so a ratio built on them is timer noise wearing a
# threshold's clothing. The absolute is the meaningful guard.
def test_select_burst_is_cheap(scaling):
    assert scaling["large"]["select_burst"] < 5.0    # ms, 64 rooms


# select_interactive: a human ctrl-clicking, one _apply_edit_actions per click.
# This is the honest model of the reported stall; the cheap-count fix carries it.
# Promoted to a HARD PASS at P0.6 -- it clears the threshold (see the log).
def test_select_interactive_scales_subquadratically(scaling):
    assert scaling["ratios"]["select_interactive"] < 8


# group_selected is near-quadratic today (ratio ~13.7 at P0.3 baseline): a room's
# walls are duplicated and the whole detection engine reruns. P3.8 (vertices own
# geometry; no duplicate_wall/coalesce on group) is where this ratio drops under
# 8. strict=False so it is free to pass early (e.g. after P0.6) without flapping.
def test_undo_latency_is_bounded(scaling):
    """P2.3 baseline for P6.1's "undo cost is independent of plan size".

    An ABSOLUTE bound, not a ratio: undo now walks the scene into the canonical
    document, and a ratio assertion this close to the threshold would flap (the
    P0.6 precedent, where select_burst was converted for the same reason).
    Generous on purpose -- this catches an order-of-magnitude regression, and
    P6.1 is where the number has to stop growing with the plan at all."""
    assert scaling["large"]["undo"] < 500.0
    assert scaling["large"]["snapshot"] < 100.0


@pytest.mark.xfail(strict=False, reason="group is ~quadratic until P3.8")
def test_group_scales_subquadratically(scaling):
    assert scaling["ratios"]["group"] < 8


def test_bake_scales_subquadratically(scaling):
    assert scaling["ratios"]["bake"] < 8


# ungroup_selected still runs a plan-wide merge on release, which is O(walls^2) BY
# CONSTRUCTION -> ungroup is genuinely super-linear. It dips under 8 at n=8 after
# P0.6 item 2 (the _oriented_box cache cut its boundingRect cost, ~8.5 -> ~5.6),
# but that pass is INCIDENTAL at this grid size and reasserts at larger n.
# Kept xfail(strict=False) -> P3.8 (P4.5 removes the call entirely): promoting
# it would encode "ungroup is fine", which is false -- only "less bad at n=8".
@pytest.mark.xfail(strict=False, reason="ungroup runs an O(walls^2) merge sweep "
                                        "until P3.8; sub-8 at n=8 is incidental")
def test_ungroup_scales_subquadratically(scaling):
    assert scaling["ratios"]["ungroup"] < 8
