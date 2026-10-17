# ruff: noqa  -- a filed measurement probe (0279-report.md)
"""Does the screen ever show something stale under MinimalViewportUpdate?

The screen under a minimal update is the previous frame with only the
repainted regions redrawn. This probe keeps exactly that: an image updated
only inside the regions of the viewport's real Paint events, and after
every move of a gesture compares it with a full render of the scene as it
is now. A pixel that differs is one the user would see stale (a trail, a
missed redraw). It also times each frame.

    python stale_probe.py <plan.json>
"""
import os
import statistics
import sys
import time

os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from PyQt6.QtCore import QEvent, QObject, QPointF, Qt
from PyQt6.QtGui import QImage, QMouseEvent, QPainter, QRegion
from PyQt6.QtWidgets import QApplication

app = QApplication([])
import FloorPlanner as fp
from floorplanner import roofs as R

LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
win = fp.MainWindow()
win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
win.resize(1600, 1000)
win.show()
win.load_path(sys.argv[1])
app.processEvents()
sc = win.scene
vp = win.view.viewport()
print("viewport update mode:", win.view.viewportUpdateMode().name, flush=True)


class Regions(QObject):
    def __init__(self):
        super().__init__()
        self.region = QRegion()
        self.grabbing = False

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.Paint and not self.grabbing:
            self.region = self.region.united(ev.region())
        return False


REG = Regions()
vp.installEventFilter(REG)


def fresh():
    REG.grabbing = True
    img = vp.grab().toImage().convertToFormat(QImage.Format.Format_RGB32)
    REG.grabbing = False
    return img


CANVAS = [None]


def sync_screen():
    """Copy the repainted regions from a full render into the emulated screen."""
    f = fresh()
    if CANVAS[0] is None or CANVAS[0].size() != f.size():
        CANVAS[0] = f.copy()
    else:
        p = QPainter(CANVAS[0])
        # QRegion is not iterable in PyQt6: clip to it and copy through
        p.setClipRegion(REG.region)
        p.drawImage(0, 0, f)
        p.end()
    REG.region = QRegion()
    return f


def stale(f):
    c = CANVAS[0]
    n = 0
    w, h = f.width(), f.height()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if c.pixel(x, y) != f.pixel(x, y):
                n += 1
    return n * 4


def send(t, sp, b, bs):
    pos = win.view.mapFromScene(sp)
    QApplication.sendEvent(vp, QMouseEvent(t, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                                           b, bs, Qt.KeyboardModifier.NoModifier))


def gesture(label, floor, press, delta, n=12, prepare=None, zoom=1.0, center=None):
    if win.active_floor != floor:
        win.switch_floor(floor)
    win.set_tool(fp.TOOL_SELECT)
    sc.clearSelection()
    if prepare:
        prepare()
    win.view.resetTransform()
    win.view.scale(zoom, zoom)
    win.view.centerOn(center or press)
    app.processEvents()
    REG.region = QRegion()
    CANVAS[0] = None
    sync_screen()
    worst, frames = 0, []
    send(QEvent.Type.MouseButtonPress, press, LEFT, LEFT)
    app.processEvents()
    sync_screen()
    for i in range(1, n + 1):
        q = QPointF(press.x() + delta[0] * i, press.y() + delta[1] * i)
        a = time.perf_counter()
        send(QEvent.Type.MouseMove, q, NONE, LEFT)
        app.processEvents()
        frames.append(time.perf_counter() - a)
        worst = max(worst, stale(sync_screen()))
    send(QEvent.Type.MouseButtonRelease, q, LEFT, NONE)
    app.processEvents()
    app.processEvents()                            # the release's repaint, one turn on
    after = stale(sync_screen())
    end = time.perf_counter() + 0.4                # the settle walk
    while time.perf_counter() < end:
        app.processEvents()
    settled = stale(sync_screen())
    print(f"  {label:<38} frame {statistics.median(frames) * 1000:6.1f} ms | stale px: worst mid-drag "
          f"{worst:6d}, after release {after:6d}, after settle {settled:6d}", flush=True)
    return worst, after, settled


items = sc.items()
def pick(cls, floor, pred=lambda it: True):
    return next(it for it in items if isinstance(it, cls) and getattr(it, "floor", None) == floor
                and pred(it))


from PyQt6.QtWidgets import QGraphicsView
MODE = os.environ.get("FP_PROBE_MODE", "minimal")
if MODE == "full":
    win.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
print("probing with", win.view.viewportUpdateMode().name, flush=True)
rows = []
# a wall's body (slides it), on each floor
for fl in ("default", "upper"):
    w = pick(fp.WallItem, fl, lambda w: w.length() > 96 and w.wall_type == "interior")
    mid = QPointF((w.p1.x() + w.p2.x()) / 2, (w.p1.y() + w.p2.y()) / 2)
    u = w.unit()
    rows.append(gesture(f"wall body slide ({fl})", fl, mid, (-u.y() * 3, u.x() * 3)))
    w = pick(fp.WallItem, fl, lambda w: w.length() > 96)
    rows.append(gesture(f"wall end stretch ({fl})", fl, QPointF(w.p2), (w.unit().x() * 3, w.unit().y() * 3),
                        prepare=lambda w=w: w.setSelected(True)))
# a room by its name
room = pick(fp.RoomItem, "upper")
lab = room.mapToScene(room._label_rect().center())
rows.append(gesture("room drag by its name (upper)", "upper", lab, (3, 2)))
# a furnishing
f = pick(fp.FurnishingItem, "default")
rows.append(gesture("furnishing drag (default)", "default", f.scenePos(), (4, 2)))
# an opening along its wall
op = next(o for w in items if isinstance(w, fp.WallItem) and w.floor == "default" for o in w.openings)
u = op.wall.unit()
rows.append(gesture("opening slide (default)", "default", op.scenePos(), (u.x() * 3, u.y() * 3)))
# roof grips
win._set_show_roofs(True)
win._set_edit_roofs(True)
roofs = [r for r in items if isinstance(r, R.RoofItem)]
main = max((r for r in roofs if r.floor == "upper" and not r.is_dormer()), key=lambda r: r.length())
def grip_of(roof, kind):
    return next(g for g in roof.grips if g.kind == kind)
ux, uy, nx, ny = main._axis()
rows.append(gesture("roof ridge grip (upper main)", "upper", grip_of(main, "ridge").scenePos(),
                    (nx * 3, ny * 3), prepare=lambda: main.setSelected(True)))
dm = next(r for r in roofs if r.is_dormer() and r.floor == "upper")
dx, dy, dnx, dny = dm._axis()
rows.append(gesture("dormer eave grip (upper)", "upper", grip_of(dm, "eave_l").scenePos(), (dnx * 2, dny * 2),
                    prepare=lambda: dm.setSelected(True)))
garage = next(r for r in roofs if r.is_dormer() and r.floor == "default")
gx, gy, _, _ = garage._axis()
rows.append(gesture("garage back-end knob (default)", "default", grip_of(garage, "end_1").scenePos(),
                    (-gx * 3, -gy * 3), prepare=lambda: garage.setSelected(True)))
# zoomed in: a wall body at 3x
w = pick(fp.WallItem, "default", lambda w: w.length() > 96 and w.wall_type == "interior")
mid = QPointF((w.p1.x() + w.p2.x()) / 2, (w.p1.y() + w.p2.y()) / 2)
u = w.unit()
rows.append(gesture("wall body slide, zoom 3x (default)", "default", mid, (-u.y() * 2, u.x() * 2), zoom=3.0))
print("\nmax stale after release over all gestures:", max(r[1] for r in rows),
      "| after settle:", max(r[2] for r in rows), flush=True)
os._exit(0)
