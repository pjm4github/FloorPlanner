"""P0.3 scaling harness — measures the group/bake/ungroup/rebuild hot paths at
two plan sizes and records how they scale.

Builds an n x n grid of walled, *named* rooms that share their edge walls, each
with a door, a window and two furnishings, at n=4 (16 rooms) and n=8 (64 rooms).
Raw milliseconds and the ratio t(2n)/t(n) are printed and emitted as a warning
so they surface in `pytest -ra`; the numbers feed the Progress log.

**THE RATIOS ARE RECORDED, NEVER ASSERTED — the flap-class ruling, P3.8.**

Every timing assertion here is now an ABSOLUTE bound at the large grid. That is
not a new idea: this file already converted two ops for exactly this reason and
wrote the reason down — `select_burst` at P0.6 (*"the numbers here sit at the
perf_counter floor, so a ratio built on them is timer noise wearing a
threshold's clothing"*) and `undo` at P2.3. P3.8 applies that precedent to the
whole class rather than to whichever member last misbehaved.

**The evidence, measured over 7 identical runs per tree (P3.8):**

| | ratio spread | absolute spread at n=8 |
|---|---|---|
| the four big ops | 1.06–1.70× | **1.03–1.15×** |
| `select_interactive` at `2c5fd8d` | **21.98×** (1.22 … 26.82) | 6.95× |
| `rebuild` on HEAD | 2.12× | 1.2× |

**The diagnosis, which is why no threshold could have fixed it:** the n=4 leg is
0.2–4 ms, so a ratio divides one noise-dominated number by another and doubles
its exposure. The noise band (up to ~27) swallows the entire diagnostic range
the ratio exists to read — 4 ≈ linear, 8 = the threshold, 16 ≈ quadratic. A
wider threshold cannot separate signal from noise when the noise is wider than
the signal; only a different measurement can, and the absolute is it.

**Consequence for what these tests can catch.** An absolute bound catches a
BLOW-UP, not a drift: the bounds below are set roughly an order of magnitude
above the measured medians, and `bake`'s is set so a return to the pre-Phase-3
cost trips it. Drift is caught by the recorded numbers being compared at the
tasks that care — which is what P0.3b already ruled this harness is for: *"a
local gate, invoked explicitly at P0.6 and P3.8 — the two moments its numbers
decide something."* `tools/gate.py --perf` is that invocation.

This is by far the largest thing in the suite (the 64-room grid), so it stays
behind `@pytest.mark.slow` + `@pytest.mark.perf`; `--quick` skips it and
`tools/gate.py` no longer runs it at all, in any mode.
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
        if w.openings or w.length() < CELL - 12:
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


# P3.8 -- THE RATIO IS RECORDED, THE ABSOLUTE IS ASSERTED. See the class ruling
# in the module docstring: a ratio whose small leg is 1 ms is a quotient of two
# noise-dominated numbers, and the same seven runs that put this ratio at 2.61
# spread it 2.12x. The absolute at 64 rooms spreads 1.2x on the same data.
def test_rebuild_is_bounded(scaling):
    assert scaling["large"]["rebuild"] < 40.0        # ms; measured median 2.6


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
# P3.8: THE FOURTH FLAP MEMBER, and the one that turned the gate red -- 1 of 8
# and 2 of 8 in two sweeps, and at 2c5fd8d its RATIO ranged 1.22 .. 26.82 across
# seven identical runs while its absolute spread 6.95x. Converted, like its two
# predecessors, to the bound that the measurement can actually support.
def test_select_interactive_is_bounded(scaling):
    assert scaling["large"]["select_interactive"] < 100.0   # median 9.5


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


# group stays ~quadratic (ratio 12.43 at P3.8, against 12.77 before Phase 3 --
# Phase 3 did not touch it). NO XFAIL ANY MORE, because there is no ratio
# assertion left to xfail: the fact is RECORDED in the log and in the printed
# report, and what remains here is the catastrophic bound. Making a
# known-quadratic op's ratio an expected-failure was how that fact used to be
# carried; carrying it in prose is honest, and it stops the marker from
# flapping between xfail and xpass on machine load alone.
def test_group_is_bounded(scaling):
    assert scaling["large"]["group"] < 1200.0        # median 356


# bake is Phase 3's headline: 279.0 -> 26.4 ms at 64 rooms. The bound is set so
# a return to the pre-Phase-3 cost TRIPS it -- the one regression here that
# would matter most, caught by an absolute where the ratio (6.81 -> 4.09) would
# have looked merely "still under 8".
def test_bake_is_bounded(scaling):
    assert scaling["large"]["bake"] < 200.0          # median 26.4; pre-P3 279.0


# ungroup_selected still runs a plan-wide merge on release, which is O(walls^2) BY
# CONSTRUCTION -> ungroup is genuinely super-linear. It dips under 8 at n=8 after
# P0.6 item 2 (the _oriented_box cache cut its boundingRect cost, ~8.5 -> ~5.6),
# but that pass is INCIDENTAL at this grid size and reasserts at larger n.
# Kept xfail(strict=False) -> P3.8 (P4.5 removes the call entirely): promoting
# it would encode "ungroup is fine", which is false -- only "less bad at n=8".
# ungroup: 2.9x faster absolutely since Phase 3 (292.5 -> 99.8 ms) while its
# RATIO worsened past the threshold (6.89 -> 8.64). Both are true, which is
# precisely why the ratio was a poor gate -- it would now fail while the op got
# three times faster. Recorded in the log; bounded here.
def test_ungroup_is_bounded(scaling):
    assert scaling["large"]["ungroup"] < 400.0       # median 99.8; pre-P3 292.5
