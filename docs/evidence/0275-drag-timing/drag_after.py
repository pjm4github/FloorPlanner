# ruff: noqa  -- a filed measurement probe (0275-report.md), kept as it was run
"""Where a frame goes, and what each candidate fix buys. No profiler: wall
clock only. Variants are monkeypatches, applied cumulatively, each measured
on the same drag.   python drag_experiments.py <plan.json>"""
import os
import statistics
import sys
import time

os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QGraphicsView

app = QApplication([])
import FloorPlanner as fp
from floorplanner import roofs as R
from floorplanner import walls as W

PLAN = sys.argv[1]
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
MOVES = 30

win = fp.MainWindow()
win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
win.resize(1600, 1000)
win.show()
win.load_path(PLAN)
app.processEvents()
sc = win.scene
roofs = [it for it in sc.items() if isinstance(it, R.RoofItem)]
main = sorted([r for r in roofs if not r.is_dormer() and r.floor == "upper"] or
              [r for r in roofs if not r.is_dormer()], key=lambda r: -r.length())[0]
dormers = [r for r in roofs if r.is_dormer()]

COUNT = {"paint": 0, "commit": 0, "trace": 0, "spans": 0}
_bg = type(win.view).drawBackground


def bg(self, painter, rect):
    COUNT["paint"] += 1
    return _bg(self, painter, rect)


type(win.view).drawBackground = bg
_commit = type(win)._commit_if_changed


def commit(self):
    COUNT["commit"] += 1
    return _commit(self)


type(win)._commit_if_changed = commit
# the timer holds the bound method it was connected with: reconnect
win._dirty_timer.timeout.disconnect()
win._dirty_timer.timeout.connect(win._commit_if_changed)
win._dirty_timer.timeout.connect(win._update_totals)


def send(etype, sp, button, buttons):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(sp)
    QApplication.sendEvent(vp, QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                                           button, buttons, Qt.KeyboardModifier.NoModifier))


def ms(xs):
    return statistics.median(xs) * 1000


def idle():
    win.view.viewport().repaint()
    ts = []
    for _ in range(12):
        a = time.perf_counter()
        win.view.viewport().repaint()
        ts.append(time.perf_counter() - a)
    return ms(ts)


def setup(roof):
    if win.active_floor != roof.floor:
        win.switch_floor(roof.floor)
    win._set_show_roofs(True)
    win._set_edit_roofs(True)
    sc.clearSelection()
    roof.setSelected(True)
    win.view.resetTransform()
    win.view.centerOn(roof.sceneBoundingRect().center())
    app.processEvents()


def drag(roof, kind, step, realtime=True):
    """A drag as the user's machine runs it: the move is delivered, then the
    event loop runs until it is idle (the paint the scene asked for, any
    timer that came due). `realtime`: wall-clock timers, as in the app."""
    setup(roof)
    grip = next(g for g in roof.grips if g.kind == kind)
    p = grip.scenePos()
    ux, uy, nx, ny = roof._axis()
    d = (nx, ny) if kind in ("ridge", "eave_l", "eave_r") else (ux, uy)
    for k in COUNT:
        COUNT[k] = 0
    frames = []
    send(QEvent.Type.MouseButtonPress, p, LEFT, LEFT)
    for i in range(1, MOVES + 1):
        k = step * (i if i <= MOVES // 2 else MOVES - i)
        a = time.perf_counter()
        send(QEvent.Type.MouseMove, QPointF(p.x() + d[0] * k, p.y() + d[1] * k), NONE, LEFT)
        app.processEvents()
        frames.append(time.perf_counter() - a)
    c = dict(COUNT)
    a = time.perf_counter()
    send(QEvent.Type.MouseButtonRelease, p, LEFT, NONE)
    app.processEvents()
    rel = (time.perf_counter() - a) * 1000
    end = time.perf_counter() + 0.4
    while time.perf_counter() < end:
        app.processEvents()
    return ms(frames), max(frames) * 1000, c, rel


def row(label, roof, kind, step):
    m, mx, c, rel = drag(roof, kind, step)
    print(f"  {label:<34} frame {m:7.1f} ms  ({1000 / m:5.1f} fps, worst {mx:5.0f}) | "
          f"paints/move {c['paint'] / MOVES:.2f} | settle walks mid-drag {c['commit']:2d}/{MOVES} | "
          f"release {rel:5.0f} ms", flush=True)
    return m


def table(title):
    print(f"\n### {title}", flush=True)
    print(f"  idle full repaint: {idle():.1f} ms", flush=True)
    row("main roof, ridge grip", main, "ridge", 3.0)
    row("main roof, eave grip", main, "eave_l", 3.0)
    if dormers:
        row("dormer, eave grip", dormers[0], "eave_l", 2.0)
        row("dormer, ridge grip", dormers[0], "ridge", 2.0)


# --------------------------------------------------------------------------
# what one settle walk costs, alone
setup(main)
ts = []
for _ in range(5):
    a = time.perf_counter()
    win.snapshot()
    ts.append(time.perf_counter() - a)
print(f"one snapshot() (the settle walk's document): {ms(ts):.0f} ms", flush=True)
a = time.perf_counter()
R.sync_roof_clips(sc)
print(f"one sync_roof_clips (compose the building, {len(roofs)} roofs): "
      f"{(time.perf_counter() - a) * 1000:.0f} ms", flush=True)

# what the repaint is made of: paint each class's items alone
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QStyleOptionGraphicsItem
img = QImage(1600, 1000, QImage.Format.Format_ARGB32_Premultiplied)
by = {}
for it in sc.items():
    if not it.isVisible():
        continue
    p = QPainter(img)
    p.setTransform(it.sceneTransform())
    a = time.perf_counter()
    it.paint(p, QStyleOptionGraphicsItem(), None)
    dt = time.perf_counter() - a
    p.end()
    k = type(it).__name__
    n, t = by.get(k, (0, 0.0))
    by[k] = (n + 1, t + dt)
print("paint() cost by item class, one pass over the visible scene:", flush=True)
for k, (n, t) in sorted(by.items(), key=lambda kv: -kv[1][1]):
    print(f"  {k:<22} {n:4d} items  {t * 1000:8.1f} ms  ({t * 1000 / n:6.2f} ms each)", flush=True)

table("AFTER 0276 (the code on this branch, no monkeypatches)")

os._exit(0)
