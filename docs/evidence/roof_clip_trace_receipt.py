"""R5a's own picture (0186-ruling.md sec2): the clip trace ON THE ROOF,
beside the R3b wall dashes it must hug. His check runs on wiscaway with
roofs on; no wiscaway-with-roofs file exists in the repo, so this is a
synthetic house with the same ingredients -- two rooms of DIFFERENT
ceilings (96in and 120in, wiscaway's own two values) side by side under
one gable roof whose west end is a hip, exterior walls around, an
interior wall between. Eaves 80 / ridge 150 over a 24ft-wide house, so
the trace sits well inside the footprint rather than on the eave lines.

What the picture should show: the orange dashes on each wall (R3b) ending
exactly where the orange dashed trace on the roof crosses that wall; the
trace stepping outward where the 120in room begins (a taller ceiling is
hit lower down the slope, nearer the eaves); the hip end's cross segment
closing the loop on the west; and no trace over the 120in room's south
half if the eaves clear it there. Plain 2D `QGraphicsScene` painting, so
`QT_QPA_PLATFORM=offscreen` is fine (fp3d's GL path is the one that is
not -- D77/D78).

    python docs/evidence/roof_clip_trace_receipt.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QPointF, QRectF, Qt          # noqa: E402
from PyQt6.QtGui import QImage, QPainter, QPainterPath  # noqa: E402
from PyQt6.QtWidgets import QApplication, QGraphicsScene  # noqa: E402

_app = QApplication.instance() or QApplication([])

from floorplanner.config import DEFAULT_FLOOR      # noqa: E402
from floorplanner.roofs import RoofItem, roof_clip_spans, roof_clip_trace  # noqa: E402
from floorplanner.rooms import RoomItem            # noqa: E402
from floorplanner.walls import WallItem            # noqa: E402

# the house: x 0..480 (40ft), y 0..288 (24ft); ridge along x at y=144
X0, X1, Y0, Y1 = 0.0, 480.0, 0.0, 288.0
SPLIT_X = 300.0                 # the interior wall between the two rooms
RIDGE_Y = (Y0 + Y1) / 2.0


def _room(scene, x0, x1, name, ceiling):
    path = QPainterPath()
    path.addRect(x0, Y0, x1 - x0, Y1 - Y0)
    room = RoomItem(name, QPointF((x0 + x1) / 2.0, RIDGE_Y), path,
                    (x1 - x0) * (Y1 - Y0) / 144.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling
    scene.addItem(room)
    return room


def build_scene():
    scene = QGraphicsScene()
    _room(scene, X0, SPLIT_X, "Living 96in", 96.0)
    _room(scene, SPLIT_X, X1, "Great room 120in", 120.0)
    walls = []
    for p1, p2, kind in (
            ((X0, Y0), (X1, Y0), "exterior"), ((X1, Y0), (X1, Y1), "exterior"),
            ((X1, Y1), (X0, Y1), "exterior"), ((X0, Y1), (X0, Y0), "exterior"),
            ((SPLIT_X, Y0), (SPLIT_X, Y1), "interior")):
        w = WallItem(QPointF(*p1), QPointF(*p2), kind)
        w.floor = DEFAULT_FLOOR
        scene.addItem(w)
        walls.append(w)
    roof = RoofItem(QPointF(X0, RIDGE_Y), QPointF(X1, RIDGE_Y), eaves_h_in=80.0,
                    ridge_h_in=150.0, overhang_in=12.0, span_in=RIDGE_Y - Y0,
                    gable=[False, True])
    roof.floor = DEFAULT_FLOOR
    scene.addItem(roof)
    return scene, walls, roof


def main():
    scene, walls, roof = build_scene()
    for w in walls:
        spans = roof_clip_spans(scene, w)
        if spans:
            print(f"wall ({w.p1.x():.0f},{w.p1.y():.0f}) -> "
                  f"({w.p2.x():.0f},{w.p2.y():.0f}): dashed {spans}")
    for p, q in roof_clip_trace(scene, roof):
        print(f"trace ({p.x():.2f},{p.y():.2f}) -> ({q.x():.2f},{q.y():.2f})")

    img = QImage(900, 560, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    pr = QPainter(img)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(pr, QRectF(0, 0, 900, 560), QRectF(-120, -40, 660, 380),
                 Qt.AspectRatioMode.KeepAspectRatio)
    pr.end()
    out = os.path.join(os.path.dirname(__file__), "roof-clip-trace-r5a.png")
    img.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
