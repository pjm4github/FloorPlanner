#!/usr/bin/env python3
"""STAGE ONE: find the PRODUCER of accumulating vertices.

    python docs/evidence/vertex_accumulation_probe.py <plan.json> [room]

Counts vertices and walls before and after ONE room move and ONE shuffled room
move, driven as REAL GESTURES through the view — a label-drag is
extract → translate → join, and that whole path is what the user runs.

**Attribution, not just a delta.** Every `Vertex.at` (the mint) and every split /
merge / weld entry point is wrapped and recorded WITH ITS CALLER, so the report
can name the call site rather than leaving "something added twelve vertices".

WHAT IT DOES NOT DO: it does not clean anything, and it must not. A leak a
cleaner hides is worse than a leak that shows.
"""
import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
PLAN = os.path.abspath(sys.argv[1])
ROOM = sys.argv[2] if len(sys.argv) > 2 else None

from PyQt6.QtCore import QEvent, QPointF, Qt          # noqa: E402
from PyQt6.QtGui import QMouseEvent                    # noqa: E402
from PyQt6.QtWidgets import QApplication               # noqa: E402

app = QApplication([])
import FloorPlanner as fp                              # noqa: E402
import floorplanner.extract as X                       # noqa: E402
import floorplanner.rooms as R                         # noqa: E402
import floorplanner.vertex as V                        # noqa: E402
import floorplanner.walls as W                         # noqa: E402

CALLS = []          # (label, caller) in order


def caller_of(depth=2):
    f = sys._getframe(depth)
    return f"{os.path.basename(f.f_code.co_filename)}:{f.f_lineno} {f.f_code.co_name}"


def wrap_fn(mod, name, label):
    orig = getattr(mod, name, None)
    if orig is None:
        return

    def w(*a, **k):
        CALLS.append((label, caller_of()))
        return orig(*a, **k)
    setattr(mod, name, w)


# THE MINT ITSELF -------------------------------------------------------------
_at = V.Vertex.at.__func__


def at(cls, p):
    CALLS.append(("Vertex.at", caller_of()))
    return _at(cls, p)


V.Vertex.at = classmethod(at)
for m in (W, R, X):
    m.Vertex = V.Vertex

# the operations that create or remove corners -------------------------------
# WRAP EVERY MODULE THAT HOLDS A REFERENCE, not just the defining one.
# `extract.py:29` does `from floorplanner.walls import split_wall_at, ...`, so
# patching `walls.split_wall_at` alone left extract's own name bound to the
# original and the split went unrecorded -- the first run of this probe reported
# no split at all. Same family as "grep for identifiers, parse for shapes":
# a wrapper is only as good as the reference it is bound to.
for nm in ("split_wall_at", "split_body_landings", "merge_wall", "merge_all",
           "weld_wall_ends", "weld_scene", "normalize_walls"):
    for mod in (W, X, R):
        if hasattr(mod, nm):
            wrap_fn(mod, nm, f"walls.{nm} (via {mod.__name__.split('.')[-1]})")
for mod, nm in [(R, "split_partially_covered_edges"),
                (X, "extract_room"), (X, "join_room")]:
    wrap_fn(mod, nm, f"{mod.__name__.split('.')[-1]}.{nm}")


def census(win):
    """Distinct Vertex OBJECTS the plan holds, plus walls and rooms."""
    walls = [i for i in win.scene.items() if isinstance(i, fp.WallItem)]
    rooms = [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]
    vs = {}
    def add(v):
        if isinstance(v, V.Vertex):      # outline edges can hold other things
            vs[id(v)] = v
    for w in walls:
        # `w.v1` is the UID STRING, not the object -- `_v1` / `_v2` hold the
        # Vertex. Reading `v1` here silently dropped every wall corner and made
        # the first run of this probe report degree2 = 0 on a 103-wall plan.
        add(w._v1)
        add(w._v2)
    for r in rooms:
        for e in r.outline:
            add(getattr(e, "v", None))
    # coordinate-distinct points, so "12 handles on one straight run" is visible
    pts = {(round(v.x, 3), round(v.y, 3)) for v in vs.values()}

    # DEGREE-2 COLLINEAR: the vertices a coalesce would dissolve, and the
    # direct measure of "a straight run carrying a dozen handles".
    inc = {}
    for w in walls:
        for v in (w._v1, w._v2):
            if isinstance(v, V.Vertex):
                inc.setdefault(id(v), []).append(w)
    import math
    deg2 = collinear = 0
    for ws in inc.values():
        if len(ws) != 2:
            continue
        deg2 += 1
        a, b = ws
        ua = math.atan2(a.p2.y() - a.p1.y(), a.p2.x() - a.p1.x())
        ub = math.atan2(b.p2.y() - b.p1.y(), b.p2.x() - b.p1.x())
        d = abs((ua - ub) % math.pi)
        if min(d, math.pi - d) < math.radians(0.5):
            collinear += 1
    return {"walls": len(walls), "rooms": len(rooms),
            "vertex_objects": len(vs), "distinct_points": len(pts),
            "degree2": deg2, "degree2_collinear": collinear}


def gesture(win, room, dx, dy):
    """A real label-drag: press the label, move, release."""
    vp = win.view.viewport()
    start = win.view.mapFromScene(room.mapToScene(room._label_rect().center()))
    steps = 3

    def send(t, pt, btn, btns):
        QApplication.sendEvent(vp, QMouseEvent(
            t, QPointF(pt), vp.mapToGlobal(QPointF(pt)), btn, btns,
            Qt.KeyboardModifier.NoModifier))
        app.processEvents()

    send(QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton,
         Qt.MouseButton.LeftButton)
    for k in range(1, steps + 1):
        send(QEvent.Type.MouseMove,
             start + type(start)(int(dx * k / steps), int(dy * k / steps)),
             Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton)
    send(QEvent.Type.MouseButtonRelease, start + type(start)(int(dx), int(dy)),
         Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton)


out = {"plan": os.path.basename(PLAN)}
win = fp.MainWindow()
win.resize(1400, 1000)
win.show()
win.load_path(PLAN)
win.zoom_fit()
win.set_tool(fp.TOOL_SELECT)
app.processEvents()

rooms = sorted((i for i in win.scene.items() if isinstance(i, fp.RoomItem)),
               key=lambda r: -r.area_sqft)
target = next((r for r in rooms if r.name == ROOM), rooms[0])
out["room"] = target.name
out["loaded"] = census(win)

PLAN_ONLY = os.environ.get("PLAN_ONLY")
if PLAN_ONLY:
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
    raise SystemExit(0)

seq = [("move #1 (out)", False, 40, 30), ("move #2 (back)", False, -40, -30)]
# A ROOM THAT WALKS. The pair above returns the room to where it started, so a
# split made on the way out is unmade on the way back -- which is why it
# balances and why it says nothing about a real editing session. These land the
# room somewhere NEW each time, which is what dragging a room about actually
# does.
seq += [(f"walk #{i}", False, 18, 0) for i in range(1, 7)]
seq += [(f"shuffle walk #{i}", True, 18, 0) for i in range(1, 4)]
for label, shuffle, dx, dy in seq:
    fp.SETTINGS["shuffle"] = shuffle
    CALLS.clear()
    before = census(win)
    gesture(win, target, dx, dy)
    after = census(win)
    seen = {}
    for lab, who in CALLS:
        seen.setdefault(lab, {}).setdefault(who, 0)
        seen[lab][who] += 1
    out[label] = {
        "shuffle": shuffle,
        "before": before, "after": after,
        "delta": {k: after[k] - before[k] for k in before},
        "calls": {k: v for k, v in sorted(
            seen.items(), key=lambda kv: -sum(kv[1].values()))},
    }

fp.SETTINGS["shuffle"] = False
json.dump(out, sys.stdout, indent=1)
sys.stdout.write("\n")
