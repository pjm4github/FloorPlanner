# ruff: noqa  -- a filed measurement probe (0275-report.md), kept as it was run
"""Timing of a roof-grip and a dormer-grip drag on a multi-floor plan.

Drives the REAL path: mouse events through the view's viewport to the grip
item, a synchronous viewport repaint after every move (what the user's
screen costs), then the event loop (timers). Times each stage per move and
profiles the whole drag.   python drag_profile.py <plan.json> [zoom]
"""
import cProfile
import io
import os
import pstats
import statistics
import sys
import time

os.environ["QT_QPA_PLATFORM"] = "windows"       # the real raster + font engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

app = QApplication([])
import FloorPlanner as fp
from floorplanner import roofs as R

PLAN = sys.argv[1]
ZOOM = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
MOVES = 40

win = fp.MainWindow()
win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)   # paints, not shown
win.resize(1600, 1000)
win.show()
t0 = time.perf_counter()
win.load_path(PLAN)
app.processEvents()
print(f"load: {time.perf_counter() - t0:.2f} s", flush=True)

sc = win.scene
items = sc.items()
by = {}
for it in items:
    by[type(it).__name__] = by.get(type(it).__name__, 0) + 1
print("scene items:", len(items), dict(sorted(by.items(), key=lambda kv: -kv[1])[:12]), flush=True)
roofs = [it for it in items if isinstance(it, R.RoofItem)]
print("floors:", [f.name for f in win.floors], "active:", win.active_floor, flush=True)
for rf in roofs:
    print(f"  roof floor={rf.floor} form={rf.form} dormer={rf.is_dormer()} len={rf.length():.0f} "
          f"span={[round(x) for x in rf.span_in]}", flush=True)


def send(etype, sp, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(sp)
    QApplication.sendEvent(vp, QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                                           button, buttons, Qt.KeyboardModifier.NoModifier))


def med(xs):
    return statistics.median(xs) * 1000 if xs else 0.0


def drag(label, roof, kind, step, profile=False):
    """Press the roof's `kind` grip, MOVES moves of `step` scene inches each
    way along the grip's drag direction, release. Returns per-stage times."""
    if win.active_floor != roof.floor:
        win.switch_floor(roof.floor)
    win._set_show_roofs(True)
    win._set_edit_roofs(True)
    sc.clearSelection()
    roof.setSelected(True)
    win.view.resetTransform()
    win.view.scale(ZOOM, ZOOM)
    win.view.centerOn(roof.sceneBoundingRect().center())
    app.processEvents()
    grip = next(g for g in roof.grips if g.kind == kind)
    p = grip.scenePos()
    ux, uy, nx, ny = roof._axis()
    d = (nx, ny) if kind in ("ridge", "eave_l", "eave_r") else (ux, uy)
    pr = cProfile.Profile() if profile else None
    t_evt, t_paint, t_loop = [], [], []
    send(QEvent.Type.MouseButtonPress, p, LEFT, LEFT)
    if pr:
        pr.enable()
    for i in range(1, MOVES + 1):
        k = step * (i if i <= MOVES // 2 else MOVES - i)      # out, then back
        q = QPointF(p.x() + d[0] * k, p.y() + d[1] * k)
        a = time.perf_counter()
        send(QEvent.Type.MouseMove, q, NONE, LEFT)
        b = time.perf_counter()
        win.view.viewport().repaint()
        c = time.perf_counter()
        app.processEvents()
        e = time.perf_counter()
        t_evt.append(b - a); t_paint.append(c - b); t_loop.append(e - c)
    if pr:
        pr.disable()
    a = time.perf_counter()
    send(QEvent.Type.MouseButtonRelease, p, LEFT, NONE)
    rel = time.perf_counter() - a
    a = time.perf_counter()
    win.view.viewport().repaint()
    rel_paint = time.perf_counter() - a
    a = time.perf_counter()
    # let the 180 ms settle timer fire: the commit walk
    end = time.perf_counter() + 0.5
    while time.perf_counter() < end:
        app.processEvents()
    settle = time.perf_counter() - a - 0.5
    tot = [x + y + z for x, y, z in zip(t_evt, t_paint, t_loop)]
    print(f"\n== {label}  (zoom {ZOOM}, {MOVES} moves) ==", flush=True)
    print(f"  per move, median ms: handler {med(t_evt):7.1f} | repaint {med(t_paint):7.1f} | "
          f"event loop {med(t_loop):7.1f} | TOTAL {med(tot):7.1f}  (max {max(tot) * 1000:.0f})", flush=True)
    print(f"  => {1000.0 / max(med(tot), 1e-6):.1f} frames/s while dragging", flush=True)
    print(f"  release: handler {rel * 1000:.0f} ms, repaint {rel_paint * 1000:.0f} ms", flush=True)
    if pr:
        s = io.StringIO()
        st = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        st.print_stats(45)
        txt = s.getvalue()
        print(txt[txt.index("ncalls"):][:9000], flush=True)
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(22)
        txt = s.getvalue()
        print("-- by own time --\n" + txt[txt.index("ncalls"):][:4500], flush=True)
    return med(t_evt), med(t_paint), med(t_loop)


mains = sorted([r for r in roofs if not r.is_dormer()], key=lambda r: -r.length())
dormers = [r for r in roofs if r.is_dormer()]
main = mains[0]
drag("MAIN ROOF, ridge grip", main, "ridge", 3.0, profile=True)
drag("MAIN ROOF, end grip", main, "end_1", 3.0)
drag("MAIN ROOF, eave grip", main, "eave_l", 3.0)
if dormers:
    dm = dormers[0]
    drag(f"DORMER ({dm.form}), eave grip", dm, "eave_l", 2.0, profile=True)
    drag(f"DORMER ({dm.form}), ridge grip", dm, "ridge", 2.0)

# the baseline: what one repaint of this view costs with NOTHING changing
win.view.viewport().repaint()
ts = []
for _ in range(20):
    a = time.perf_counter()
    win.view.viewport().repaint()
    ts.append(time.perf_counter() - a)
print(f"\nidle full-viewport repaint: median {med(ts):.1f} ms", flush=True)
os._exit(0)
