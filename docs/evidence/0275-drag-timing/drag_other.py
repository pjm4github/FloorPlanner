# ruff: noqa  -- a filed measurement probe (0275-report.md), kept as it was run
import os, statistics, sys, time
os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication
app = QApplication([])
import FloorPlanner as fp
from floorplanner import roofs as R
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
win = fp.MainWindow(); win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
win.resize(1600, 1000); win.show()
win.load_path(sys.argv[1]); app.processEvents()
sc = win.scene
def send(t, sp, b, bs):
    vp = win.view.viewport(); pos = win.view.mapFromScene(sp)
    QApplication.sendEvent(vp, QMouseEvent(t, QPointF(pos), QPointF(vp.mapToGlobal(pos)), b, bs, Qt.KeyboardModifier.NoModifier))
def idle():
    win.view.viewport().repaint(); ts = []
    for _ in range(10):
        a = time.perf_counter(); win.view.viewport().repaint(); ts.append(time.perf_counter() - a)
    return statistics.median(ts) * 1000
def furn_drag():
    f = next(it for it in sc.items() if isinstance(it, fp.FurnishingItem) and it.floor == win.active_floor and it.isVisible())
    sc.clearSelection(); win.set_tool(fp.TOOL_SELECT)
    win.view.resetTransform(); win.view.centerOn(f.scenePos()); app.processEvents()
    p = f.scenePos(); fr = []
    send(QEvent.Type.MouseButtonPress, p, LEFT, LEFT)
    for i in range(1, 25):
        a = time.perf_counter()
        send(QEvent.Type.MouseMove, QPointF(p.x() + 2 * i, p.y() + i), NONE, LEFT); app.processEvents()
        fr.append(time.perf_counter() - a)
    send(QEvent.Type.MouseButtonRelease, QPointF(p.x(), p.y()), LEFT, NONE); app.processEvents()
    return statistics.median(fr) * 1000
nroof = sum(1 for it in sc.items() if isinstance(it, R.RoofItem))
print(f"roofs {nroof}; active floor {win.active_floor}")
for show, edit, label in ((True, True, "Show roof ON, Edit roof ON"), (True, False, "Show roof ON, Edit roof OFF"), (False, False, "Show roof OFF")):
    win._set_show_roofs(show); win._set_edit_roofs(edit); app.processEvents()
    m = furn_drag()
    print(f"  {label:<30} idle repaint {idle():6.1f} ms | furnishing drag frame {m:6.1f} ms ({1000/m:5.1f} fps)", flush=True)
win._set_show_roofs(True); win._set_edit_roofs(True)
for fl in [f.name for f in win.floors]:
    win.switch_floor(fl); app.processEvents()
    print(f"  floor {fl:<10} (roofs shown) idle repaint {idle():6.1f} ms", flush=True)
os._exit(0)
