# ruff: noqa  -- a filed measurement probe (0276-report.md)
"""Count settle walks and repaints while the app sits idle, after a load and
after a drag.   python drag_idle.py <plan.json>"""
import os, sys, time
os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication
app = QApplication([])
import FloorPlanner as fp
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
win = fp.MainWindow(); win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
win.resize(1600, 1000); win.show(); win.load_path(sys.argv[1]); app.processEvents()
n = {"c": 0, "paint": 0}
real = win._commit_if_changed
def counted():
    n["c"] += 1; real()
win._commit_if_changed = counted
bg = type(win.view).drawBackground
def cbg(self, p, r):
    n["paint"] += 1; return bg(self, p, r)
type(win.view).drawBackground = cbg
def idle(sec, label):
    n["c"] = 0; n["paint"] = 0
    end = time.perf_counter() + sec
    while time.perf_counter() < end:
        app.processEvents(); time.sleep(0.005)
    print(f"{label:<34} {sec}s idle -> settle walks {n['c']}, repaints {n['paint']}, timer armed {win._dirty_timer.isActive()}", flush=True)
idle(2.0, "after load")
sc = win.scene
f = next(it for it in sc.items() if isinstance(it, fp.FurnishingItem) and it.floor == win.active_floor and it.isVisible())
win.view.centerOn(f.scenePos()); app.processEvents()
def send(t, sp, b, bs):
    vp = win.view.viewport(); pos = win.view.mapFromScene(sp)
    QApplication.sendEvent(vp, QMouseEvent(t, QPointF(pos), QPointF(vp.mapToGlobal(pos)), b, bs, Qt.KeyboardModifier.NoModifier))
p = f.scenePos()
send(QEvent.Type.MouseButtonPress, p, LEFT, LEFT)
for i in range(1, 10):
    send(QEvent.Type.MouseMove, QPointF(p.x() + 6 * i, p.y()), NONE, LEFT); app.processEvents()
send(QEvent.Type.MouseButtonRelease, QPointF(p.x() + 54, p.y()), LEFT, NONE)
idle(0.5, "0.5 s after a furnishing drag")
idle(2.0, "the next 2 s")
os._exit(0)
