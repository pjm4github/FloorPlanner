# ruff: noqa  -- a filed measurement probe (0280-report.md)
"""Settle an edit next to W130 on the upper floor, then time and profile
Ctrl+Z (undo) and redo.   python undo_probe.py <plan.json>"""
import cProfile, io, os, pstats, sys, time
os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication
app = QApplication([])
import FloorPlanner as fp
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
win = fp.MainWindow(); win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
win.resize(1600, 1000); win.show()
win.load_path(sys.argv[1]); app.processEvents()
sc = win.scene
win.switch_floor("upper"); win._set_edit_roofs(False); app.processEvents()
w = next(it for it in sc.items() if isinstance(it, fp.WallItem) and it.uid == "W130")
print("W130", w.floor, w.wall_type, w.p1, w.p2, flush=True)
def send(t, sp, b, bs):
    vp = win.view.viewport(); pos = win.view.mapFromScene(sp)
    QApplication.sendEvent(vp, QMouseEvent(t, QPointF(pos), QPointF(vp.mapToGlobal(pos)), b, bs, Qt.KeyboardModifier.NoModifier))
u = w.unit()
win.view.resetTransform(); win.view.centerOn(QPointF(456, 510)); app.processEvents()
def drag(a, d, label):
    before = (QPointF(w.p1), QPointF(w.p2))
    send(QEvent.Type.MouseButtonPress, a, LEFT, LEFT)
    for i in range(1, 9):
        send(QEvent.Type.MouseMove, QPointF(a.x() + d[0] * i, a.y() + d[1] * i), NONE, LEFT); app.processEvents()
    send(QEvent.Type.MouseButtonRelease, QPointF(a.x() + d[0] * 8, a.y() + d[1] * 8), LEFT, NONE)
    end = time.perf_counter() + 0.6
    while time.perf_counter() < end: app.processEvents()
    print(f"{label}: wall {before[0]},{before[1]} -> {w.p1},{w.p2}; undo depth {len(win._undo_stack)}"); print("  under press:", type(win.view.itemAt(win.view.mapFromScene(a))).__name__, flush=True)
mid = QPointF((w.p1.x() + w.p2.x()) / 2, (w.p1.y() + w.p2.y()) / 2)
drag(mid, (-u.y() * 3, u.x() * 3), "body drag")
if not win._undo_stack:
    w.setSelected(True); app.processEvents()
    drag(QPointF(w.p2), (u.x() * 3, u.y() * 3), "end drag (selected)")
print("undo stack depth", len(win._undo_stack), flush=True)
pr = cProfile.Profile()
a = time.perf_counter()
pr.enable(); win.undo(); pr.disable()
b = time.perf_counter(); app.processEvents(); c = time.perf_counter()
print(f"undo(): {(b - a) * 1000:.0f} ms (profiled), then the repaint/loop {(c - b) * 1000:.0f} ms", flush=True)
st = io.StringIO(); pstats.Stats(pr, stream=st).sort_stats("cumulative").print_stats(40)
t = st.getvalue(); print(t[t.index("ncalls"):][:9000], flush=True)
# an unprofiled undo/redo pair for the wall clock
a = time.perf_counter(); win.redo(); app.processEvents(); b = time.perf_counter()
win.undo(); app.processEvents(); c = time.perf_counter()
print(f"unprofiled: redo {(b - a) * 1000:.0f} ms, undo {(c - b) * 1000:.0f} ms", flush=True)
from floorplanner import roofs as R
import time as _t
from floorplanner.roofclip import compose_building
from floorplanner.config import floor_elevation
rs = [it for it in sc.items() if isinstance(it, R.RoofItem)]
a = _t.perf_counter(); R.sync_roof_clips(sc); b = _t.perf_counter()
print(f"one compose of the building ({len(rs)} roofs): {(b - a) * 1000:.0f} ms", flush=True)
a = _t.perf_counter(); win.snapshot(); b = _t.perf_counter()
print(f"one snapshot(): {(b - a) * 1000:.0f} ms", flush=True)
st = win._committed_state
a = _t.perf_counter(); R.hold_roof_clips(sc, True); win.load_data(st, keep_backdrop=True); c1 = _t.perf_counter(); R.hold_roof_clips(sc, False); b = _t.perf_counter()
print(f"load_data of the same state: {(c1 - a) * 1000:.0f} ms without the compose, + {(b - c1) * 1000:.0f} ms compose", flush=True)
os._exit(0)
