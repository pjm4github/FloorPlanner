# ruff: noqa  -- a filed measurement probe (0279-report.md)
"""Does every item paint inside its own boundingRect?

Under MinimalViewportUpdate the view repaints only the regions items report
as changed -- their bounding rects -- so ink outside an item's rect is left
behind as a trail when the item moves, and not drawn when the item appears.
This paints EVERY visible item of a plan alone, at the view's own scale, and
counts the pixels it inks outside its declared rect (a 1-px allowance for
antialiasing). Run at two zooms, with the item callouts on and with a
selection, so the selected-only paint paths are covered too.

    python bounds_audit.py <plan.json> [zoom ...]
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "windows"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter, QTransform
from PyQt6.QtWidgets import QApplication, QStyleOptionGraphicsItem

app = QApplication([])
import FloorPlanner as fp
from floorplanner.config import SETTINGS

PLAN = sys.argv[1]
ZOOMS = [float(z) for z in sys.argv[2:]] or [1.0, 3.0]

win = fp.MainWindow()
win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
win.resize(1600, 1000)
win.show()
win.load_path(PLAN)
SETTINGS["show_callouts"] = True
app.processEvents()
sc = win.scene


def audit(zoom, label):
    win.view.resetTransform()
    win.view.scale(zoom, zoom)
    app.processEvents()
    worst = {}
    for it in sc.items():
        if not it.isVisible():
            continue
        br = it.boundingRect()
        if br.isEmpty():
            continue
        # the item's local -> device transform at this zoom, translated so
        # the bounding rect lands at (M, M) in a padded image
        M = 120
        t = it.sceneTransform() * QTransform.fromScale(zoom, zoom)
        dev = t.mapRect(br)
        w, h = int(dev.width()) + 2 * M, int(dev.height()) + 2 * M
        if w * h > 9_000_000:
            continue
        img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(0)
        p = QPainter(img)
        p.setTransform(t * QTransform.fromTranslate(M - dev.left(), M - dev.top()))
        opt = QStyleOptionGraphicsItem()
        opt.exposedRect = br
        try:
            it.paint(p, opt, None)
        finally:
            p.end()
        x0, y0 = M - 1, M - 1
        x1, y1 = M + int(dev.width()) + 1, M + int(dev.height()) + 1
        out, far = 0, 0
        for y in range(0, h):
            row_in = y0 <= y <= y1
            for x in range(0, w):
                if row_in and x0 <= x <= x1:
                    continue
                if (img.pixel(x, y) >> 24) & 0xFF:
                    out += 1
                    far = max(far, max(x0 - x, x - x1, y0 - y, y - y1, 0))
        if out:
            k = type(it).__name__ + (":" + getattr(it, "kind", "") if hasattr(it, "kind") and isinstance(getattr(it, "kind"), str) else "")
            n, px, fr = worst.get(k, (0, 0, 0))
            worst[k] = (n + 1, max(px, out), max(fr, far))
    print(f"\n{label} (zoom {zoom}): item classes inking OUTSIDE their boundingRect", flush=True)
    if not worst:
        print("  none", flush=True)
    for k, (n, px, fr) in sorted(worst.items(), key=lambda kv: -kv[1][1]):
        print(f"  {k:<28} {n:4d} items | worst {px:6d} px outside, up to {fr:4d} px away", flush=True)
    return worst


for fl in [f.name for f in win.floors]:
    win.switch_floor(fl)
    app.processEvents()
    for z in ZOOMS:
        audit(z, f"floor {fl}, nothing selected")
    # a selection: one of each selectable kind on the floor
    sc.clearSelection()
    seen = set()
    for it in sc.items():
        k = type(it).__name__
        if k in seen or not (it.flags() & it.GraphicsItemFlag.ItemIsSelectable) or not it.isVisible():
            continue
        if getattr(it, "floor", fl) != fl:
            continue
        it.setSelected(True)
        seen.add(k)
    app.processEvents()
    for z in ZOOMS:
        audit(z, f"floor {fl}, one of each kind selected")
    sc.clearSelection()
os._exit(0)
